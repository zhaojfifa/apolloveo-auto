# PR-3 · Delivery Center Result + Publish Reframing — Implementation Report

Branch: `redesign/ms-delivery-result-publish-pr3-20260528`
Wave: Matrix Script Operator Experience Implementation — **PR-3 of 7**
Date: 2026-05-28
Rollback point: PR-2D commit

## Reading Declaration

Design plan §7 + Mission §C (six sections in canonical order: ① 交付结果介绍 / ② 主视频 / ③ 必需交付物 / ④ 可选交付物 / ⑤ 发布设置 / ⑥ 发布回填) + approved product decision #3 (publish platform uses `<datalist>` with 7 suggestions; free-text allowed; no closed enum on contract layer).

## Files changed

| File | Change | Net |
|---|---|---|
| `gateway/app/templates/task_publish_hub.html` | Reframed publish-hub matrix_script branch: header relabelled to "① · 介绍 / 交付结果介绍 · {title}"; existing op-cards op-section-indices relabelled (A→②, B→③, C→④, D→④ 文案包, E→⑥ 回填, F→⑥ 归档). NEW ⑤ 发布设置 form inserted between current Block D (copy bundle) and the renamed ⑥ 回填 block. Form has 6 fields: 发布平台 (datalist with 7 suggestions, free-text allowed), 账号, 标题, 文案, 标签, 计划发布时间. Two actions: 标记为已发布 (POSTs `operator_publish` event_kind to existing endpoint) + 跳过发布 (POSTs `operator_retract`). Honesty disclaimer "本表单不直接对外发布". | +101 / −6 |
| `gateway/app/services/tests/test_matrix_script_delivery_center_pr3_reframing.py` | NEW · 16 tests covering: 6-section index numbering, ⑤ 发布设置 form closure-endpoint POST + operator_publish event_kind reuse + 6 fields + 2 actions + 7-platform datalist (product decision #3) + honesty note + no provider/model selector + redesign-wave attr + ordering ⑤-before-⑥. | +180 |
| `gateway/app/services/tests/test_matrix_script_delivery_center_blocks_a_to_f.py` | UPDATED · `test_block_d_template_no_free_text_editing_affordance` slice end shifted from Block E to the new ⑤ 发布设置 block (the operator-typed textarea legitimately belongs to ⑤, not Block D). | +12 / −2 |
| `docs/design/screenshots/.../pr3/` | Snapshot + report. | new |

## Scope boundary

**Inside PR-3**: publish-hub matrix_script branch reframing (section indices + new ⑤ form) + tests + snapshot/report.

**Outside PR-3**: unified visual validation (PR-4).

**Bytewise unchanged**: no helper module added or modified, no wiring change, no contract / packet / closed-enum / schema change, no new endpoint (the new form POSTs to the existing `/api/matrix-script/closures/{task_id}/events` with the existing `operator_publish` event kind), no Hot Follow / Digital Anchor / Asset Supply touch, no provider/model/vendor/engine selector.

## Screenshots

Real browser HTML snapshot via Claude Preview MCP on running gateway:

| # | Capture | URL | HTML | Audit |
|---|---|---|---|---|
| 1 | Delivery Center publish hub at task `2be4843363da` with all 6 mission sections rendered | `/tasks/2be4843363da/publish` | [`01_delivery_center_six_sections_1280x900.html`](01_delivery_center_six_sections_1280x900.html) | grep `\b[①②③④⑤⑥]` returns **7 occurrences** = all 6 mission section indices present (④ appears twice: 可选 + 文案包; ⑥ appears twice: 回填 + 归档 as sub-section) ✓ |

## Tests

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_delivery_center_pr3_reframing.py \
                    gateway/app/services/tests/test_matrix_script_delivery_center_blocks_a_to_f.py
=========================== 117 passed, 1 failed pre-existing ==========================
```

The 1 failure is `test_block_d_resolved_subfield_has_status_resolved_when_caption_present` — pre-existing on `main`, unrelated to PR-3 (confirmed earlier via `git stash` round-trip).

Full wave-stack (PR-1..PR-3 + adjacent helper tests): 302+ passing.

## Explicit no-change statement

This PR does **NOT**: touch any contract under `docs/contracts/`; widen any closed enum; add any new endpoint (operator_publish + operator_retract event kinds are pre-existing in `D1_EVENT_KINDS`); add or modify any helper module; modify wiring; touch Hot Follow / Digital Anchor / Asset Supply; add provider/model/vendor/engine selector. The 发布平台 `<datalist>` is a UI suggestion mechanism (HTML standard) — free-text remains accepted, NOT a closed enum on the contract layer per approved product decision #3.

## Mission §C section mapping

| Mission section | Implementation |
|---|---|
| ① 交付结果介绍 | Existing `matrix-script-delivery-center-header` op-card with relabelled "① · 介绍" index + "交付结果介绍 · {title}" heading |
| ② 主视频 | Existing `matrix-script-block-a-final-video-primary` op-card with relabelled "② · 主视频" index |
| ③ 必需交付物 | Existing `matrix-script-block-b-required-deliverables` op-card with relabelled "③ · 必需" index |
| ④ 可选交付物 | Existing `matrix-script-block-c-scene-pack` ("④ · 可选") + `matrix-script-block-d-copy-bundle` ("④ · 文案包") |
| ⑤ 发布设置 | NEW `matrix-script-block-publish-settings` op-card with 6 fields + 2 actions + datalist + honesty note |
| ⑥ 发布回填 | Existing `matrix-script-block-e-publish-feedback` relabelled "⑥ · 回填" + `matrix-script-block-f-iteration-archive` relabelled "⑥ · 归档" (kept as a sub-section under 回填 conceptually) |

## Remaining backend limitations (unchanged)

No real outbound publishing — the ⑤ form records an in-system closure event; external publish happens manually on the platform. The honesty note makes this explicit on the operator surface.

## Matrix Script is not production-operable

Wave target unchanged.

## Rollback

`git reset --hard <PR-2D-commit>` removes the PR-3 reframe + new form + tests + snapshot/report.
