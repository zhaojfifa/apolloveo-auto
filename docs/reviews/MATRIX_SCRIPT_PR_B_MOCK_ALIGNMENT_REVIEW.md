# PR-B Mock Alignment Review

Date: 2026-06-01
Subject: PR [#190](https://github.com/zhaojfifa/apolloveo-auto/pull/190) `phase3/pr-b-matrix-script-operator-workbench-flow`
Reviewer task: compare PR-B against the original Matrix Script Workbench mock / product-flow design (not the PR-B self-report).
Verdict: **C — FAIL (structurally diverges from, and duplicates, the already-implemented mock). Must revise before merge.**

---

## 1. Original mock / design sources found

| Authority | What it defines | Status on `main` |
|---|---|---|
| `docs/design/matrix_script_workbench_wireframe_v1.md` (2026-05-07) | Result-oriented Workbench low-fi: Blocks A 任务头/目标摘要 · B 脚本结构 · C 变体策略 · D 生成/重新生成 · E 候选评审 · F 交付概览; six 10-second operator questions; backend binding table (real presenters). | implemented |
| `docs/design/matrix_script_result_oriented_ui_plan_v1.md` | Operator-visible block mapping + forbidden vocabulary + four-layer discipline. | implemented |
| `docs/design/matrix_script_workbench_product_flow_reset_v1.md` (2026-05-29) | **Final IA**: Section 1 主视频结果 (dominant, 4-value pill 未生成/生成中/待审核/可交付) · Section 2 生产流程可观测 (compact stepper, collapsed) · Section 3 可选变体 · Section 4 交付入口 (lightweight, CTA only) · Section 5 技术诊断 (collapsed; **legacy A–F retired into here**). Subtractive, not additive. | implemented |
| `docs/product/matrix_script_product_flow_v1.md` §6 | Workbench modules A 脚本结构 / B 变体 / C 预览对比 / D 校对 / E 质检. | implemented |

**No image mock is the binding authority; the binding mock is the reset-design markdown (`..._product_flow_reset_v1.md` §4) + the wireframe markdown.** Both are **already implemented in `gateway/app/templates/task_workbench.html`** by the Phase 2B/2D + reset wave (data-role anchors below).

### Decisive finding — the mock is already built on `main`

The matrix_script branch of `task_workbench.html` (pre-PR-B) already renders the full flow, bound to **real presenters**, with the reset IA + collapsed diagnostics:

| Section | data-role (line) | Bound to |
|---|---|---|
| ① 主视频结果 | `matrix-script-main-video-result` (482) | `derive_matrix_script_main_video_result` |
| ② 脚本理解 | `matrix-script-section-script-understanding` (866) | `ms_script_structure` (`derive_matrix_script_script_structure_view`) |
| ② 视频生成计划 · 故事板 | `matrix-script-section-generation-plan` (946) | script_understanding segments (Hook/Body/CTA→scenes), `data-status-code="plan_pending_upstream"` |
| ③ 视觉素材 | `matrix-script-section-visual-materials` (1076) | presenter |
| 角色/配音 | `matrix-script-section-role-voice` (1147) | presenter |
| 字幕/音乐 | `matrix-script-section-subtitle-music` (1195) | presenter |
| 可选变体 / 版本 | `matrix-script-section-optional-variants` / `-video-versions` (1299) | `ms_readable_variants` (`derive_matrix_script_readable_variants`) |
| 校对/调优 | `matrix-script-section-review-tuning` (1495) | presenter |
| ⑤ 交付入口 | `matrix-script-section-delivery-entry` (1545) | `ops_pr.publishable`; CTA → `/tasks/{id}/publish` |
| 5 · 技术诊断 (collapsed) | `op-console-ms-technical-diagnostics-fold` (1587) | retires legacy A–F here |

## 2. Comparison summary

- **Overall verdict: FAIL (structural divergence + duplication).** PR-B did **not** align the existing implemented flow to the PR-A real result. It added a **second, parallel** flow (`matrix-script-operator-flow`, `ms-flow-*`, template lines ~296–470) **above** the existing sections, driven by **hardcoded tomato fixtures** (`TOMATO_SCRIPT_UNDERSTANDING`, `TOMATO_VARIANTS`, `TOMATO_SHOTS`).
- **Strongest matches:** PR-B's Section A correctly surfaces the PR-A acceptance verdict (operator_usable / visual_semantic_match / shot_match_count / real_visual_count / delivery_candidate / official_publish_ready=false) and a working `打开视频` preview link — content the existing ① block does not yet show. The L3 acceptance projection itself is sound and provider-clean.
- **Largest gaps:**
  1. **Duplication.** The page now renders **two** main-result anchors, **two** script-understanding sections, **two** storyboards, **two** variant sections, **two** delivery entries. This is the exact additive-not-replacement anti-pattern the reset design §2.4/§3 declares a false pass.
  2. **Contradiction.** Existing ① `matrix-script-main-video-result` renders the honest "当前尚未生成主视频 / 未生成" (no real `final_video` in packet) while PR-B Section A renders "运营可用" — two conflicting answers to "is the main video ready?" on one page.
  3. **Hardcoded fixtures instead of real presenters.** PR-B's 脚本理解 and 变体 come from fixed tomato constants, so they render the **same tomato topic/product/audience and the same V1/V2/V3** for *any* matrix_script task — the wireframe binds these to `derive_matrix_script_script_structure_view` / `derive_matrix_script_readable_variants` (per-task truth). This is a truth-source regression (UI shows fixture content as if it were the task's).
  4. **No diagnostics consolidation.** PR-B added a primary section but did not place its content in / respect the existing collapsed 技术诊断 fold; it increases primary-scan content, the opposite of the reset goal.

## 3. Mock comparison matrix

| Area | Original mock / design says | PR-B implementation | Match? | Gap | Required action |
|---|---|---|---|---|---|
| Main Video Result | One dominant ① block, 4-value pill (未生成/生成中/待审核/可交付), single source `derive_matrix_script_main_video_result`; honest empty state, no fake media. | Adds a 2nd Section A (`ms-flow-main-result`) with a different vocab (运营可用/技术预览/未生成) from the PR-A staged result; existing ① still renders 未生成. | ❌ | Duplicate + contradictory anchors; vocab mismatch. | Link PR-A acceptance INTO the existing ① block; remove the parallel Section A. One main-result anchor only. |
| Script Understanding | ② `matrix-script-section-script-understanding`, real per-task `ms_script_structure` (Hook/Body/CTA/keywords/forbidden/audience/tone/duration/platform/language), collapsed supporting detail. | New `ms-flow-script-understanding` from **hardcoded** `TOMATO_SCRIPT_UNDERSTANDING`; renders fixed tomato values for every task. | ❌ | Duplicate section; fixture not task truth. | Drop the duplicate; reuse the existing presenter-bound section. |
| Storyboard / Shot Plan | ② 故事板 `matrix-script-section-generation-plan`, scenes derived from script segments, `plan_pending_upstream`, "未声明任何镜头已就绪". | New `ms-flow-storyboard`, fixed 5 tomato shots + per-shot acceptance (source/semantic/included). | ⚠️ partial | Net-new per-shot acceptance is valuable, but it duplicates the existing storyboard and is tomato-hardcoded. | Feed PR-A per-shot acceptance INTO the existing 故事板 section instead of a parallel one. |
| Material & Visual Assets | ③ `matrix-script-section-visual-materials` (presenter). | New `ms-flow-materials` (fixed asset→shot map). | ❌ | Duplicate; fixture. | Merge into existing materials section or the diagnostics fold. |
| Voice / Character | `matrix-script-section-role-voice` (presenter). | New `ms-flow-voice` (Azure/fallback from env). | ❌ | Duplicate. | Merge Azure/fallback status into the existing role-voice section. |
| Subtitles / Music | `matrix-script-section-subtitle-music` (presenter). | New `ms-flow-subtitles-music` (fixed). | ❌ | Duplicate. | Merge into existing section. |
| Variants | 变体 from real `derive_matrix_script_readable_variants` (per-task cells, why-tooltips). | Fixed `TOMATO_VARIANTS` V1/V2/V3 for every task. | ❌ | Duplicate; fixture not task truth. | Reuse existing variants section; if a "planned variant" concept is wanted, add it there, presenter-derived. |
| Delivery Entry | ⑤ lightweight 2-line + single CTA `/tasks/{id}/publish` (reset §4 Section 4). | New `ms-flow-delivery` 2-line + CTA `/tasks/connect/matrix_script/publish`. | ⚠️ partial | Duplicate of ⑤; CTA target differs (`/tasks/connect/{line}/publish` exists but is the temp connect route, not the per-task `/tasks/{id}/publish` the existing ⑤ uses). | Remove duplicate; if linking delivery candidate, extend existing ⑤. |
| Technical Diagnostics | Section 5 collapsed `<details>`; legacy A–F retired here; engineering ids only here. | PR-B added no diagnostics handling; its sections are all primary/expanded, increasing primary content. | ❌ | Opposite of subtractive goal. | Keep new content out of primary unless it replaces an existing primary block. |
| Four-layer state boundary | L4 displays derived facts; no invented truth; single publishable source; no provider/publish leakage. | Acceptance fields correctly L2/L3-derived & provider-clean ✅; BUT script-understanding/variants are hardcoded fixtures shown as task content ❌. | ⚠️ partial | Fixture-as-truth for non-tomato tasks. | Derive from real presenters; keep only the result-acceptance overlay as the PR-B-specific addition. |

## 4. Review criteria answers

1. Main Video Result dominant top? — **No (regressed):** two competing main-result anchors; PR-B's is on top but the existing ① still shows 未生成 below.
2. Page explains script→storyboard→assets→voice/subtitle/music→variants→main video? — **Already did, on main.** PR-B duplicates rather than enriches the explanation.
3. Storyboard shots linked to the current final video? — **Partially (PR-B's new value):** PR-B adds per-shot `included_in_current_video` + semantic status; but in a duplicate section, not the existing 故事板.
4. Variants linked to the same script plan vs decorative? — **Worse:** PR-B variants are hardcoded V1/V2/V3 decoration, not the per-task `readable_variants` the mock binds.
5. Delivery shows current candidate (not old package logic)? — Yes in PR-B's block, but duplicates the existing ⑤ and points at a different route.
6. UI hides provider/vendor/model/credit/provider_url? — **Yes** (view-model scan clean; tested).
7. UI avoids inventing status truth? — **Mixed:** acceptance is real; script-understanding/variants are fixture content presented as task truth.
8. Feels like an operator-driven workbench, not engineering diagnostics? — **No net gain:** the page is now *more* crowded (duplicated sections), the failure mode the reset design explicitly warns against.

## 5. Evidence

1. Original mock: `docs/design/matrix_script_workbench_product_flow_reset_v1.md` §4 (markdown mock) + `matrix_script_workbench_wireframe_v1.md` §§2–8; already-implemented sections cited by data-role + line number in §1 above.
2. PR-B rendered Workbench (operator-flow section): `docs/execution/screenshots/pr_a_tomato/pr_b_operator_flow.png`.
3. PR-B Delivery entry: visible in the same screenshot (Section H) and the existing ⑤ at template line 1545.
4. Duplication evidence: `grep -n 'data-role="matrix-script-section-\|data-role="ms-flow-' gateway/app/templates/task_workbench.html` shows both the pre-existing `matrix-script-section-*` flow AND the new `ms-flow-*` flow co-resident.

## 6. Required changes before merge

1. **Remove the parallel `matrix-script-operator-flow` (`ms-flow-*`) section.** Do not add a second flow.
2. **Link the PR-A real result into the EXISTING sections:** feed `operator_usable / visual_semantic_match / shot_match_count / real_visual_count / preview_url / delivery_candidate` into ① `matrix-script-main-video-result`, and the per-shot acceptance into ② 故事板 (`matrix-script-section-generation-plan`). One main-result anchor, one storyboard.
3. **Stop rendering hardcoded `TOMATO_SCRIPT_UNDERSTANDING` / `TOMATO_VARIANTS` as task content.** Keep the fixed tomato plan ONLY for the PR-A generation path; the Workbench's script-understanding and variants must stay bound to `derive_matrix_script_script_structure_view` / `derive_matrix_script_readable_variants`.
4. **Reconcile status vocabulary** with the reset's 4-value pill (or explicitly map operator_usable→可交付, technical_preview→待审核).
5. Keep the delivery CTA consistent with the existing ⑤ (`/tasks/{task_id}/publish`).
6. Re-run tests + re-file rendered evidence showing a SINGLE flow.

The narrow, correct PR-B is small: a presenter that overlays the PR-A acceptance onto the existing ①/② sections — not a new parallel flow.

## 7. Boundary check (PR-B as submitted)

- no schema/contract: ✅ (no contract/schema/packet files touched)
- no Hot Follow/Digital Anchor: ✅
- no artifact_storage.py: ✅
- no provider/publish leakage: ✅ (view-model token scan clean; official_publish_ready stays false)

The boundary is clean; the failure is **structural alignment**, not a guardrail breach.

## 8. Final recommendation

**C — FAIL.** Do not merge PR #190 as-is. Revise to overlay the PR-A real result onto the already-implemented ①/② sections and remove the duplicate fixture-driven flow, then re-review.
