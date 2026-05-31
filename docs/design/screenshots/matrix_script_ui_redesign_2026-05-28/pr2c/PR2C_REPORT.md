# PR-2C · Workbench Optional Variants Redesign — Implementation Report

Branch: `redesign/ms-workbench-variants-pr2c-20260528`
Wave: Matrix Script Operator Experience Implementation — **PR-2C of 7**
Date: 2026-05-28
Rollback point: PR-2B commit (`git log HEAD~1`)

## Reading Declaration

Reads from PR-2B baseline + design plan §6.4 + Mission §B.3 + approved product decision #2 (empty state is a single message, not N empty cards; verbatim wording).

## Files changed

| File | Change | Net |
|---|---|---|
| `gateway/app/templates/task_workbench.html` | Block E rewrite: visible title 候选评审 → **可选变体**, op-section-index "E · 评审" → "E · 变体", empty-state banner uses Mission §B.3 verbatim ("暂未生成变体视频" / "你可以先生成主视频，或选择同时生成多个变体。"), pill on empty state "暂未生成", pill when resolved "1 主推 + N 备选", tech note rewritten to operator-language ("本面板不展示完整成片或外部链接；完整成片在交付页面。" — removes the prior `final_video` / `publish_readiness` / `RC-R8` leak). Existing per-card review-zone forms preserved bytewise inside the resolved branch. `data-role` markers preserved for back-compat. Added `data-redesign-wave="2026-05-28-pr2c"` attribute. | +20 / −13 |
| `gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py` | NEW · 10 tests covering title rename, op-section-index update, mission-§B.3 verbatim empty state, pill rename, 1-main+N-optional pill, subtitle wording, operator-language tech note, redesign-wave attr, review-zone form preservation, data-role marker back-compat. | +112 |
| `gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py` | UPDATED · `test_block_e_empty_state_mission_copy_present` now asserts Mission §B.3 verbatim wording instead of the PR-0 wording. | +8 / −6 |

## Scope boundary

**Inside PR-2C**: Block E presentation rewrite + tests + snapshot/report.

**Outside PR-2C**: Block F simplification (PR-2D), Delivery Center (PR-3), unified visual validation (PR-4).

**Bytewise unchanged**: no helper / wiring / contract / packet / closed-enum / schema / endpoint change. The existing per-card review-zone forms (`ms-block-e-card-zone-form*`) are preserved with their exact data-role markers + closure endpoint POST.

## Screenshots

Real browser DOM probe via Claude Preview MCP on running gateway (1280×900). Inline image above. HTML snapshot:

| # | Capture | Viewport | URL | HTML | Runtime DOM probe |
|---|---|---|---|---|---|
| 1 | Workbench Block E rewritten as 可选变体 with Mission §B.3 empty state | 1280×900 | `/tasks/2be4843363da` | [`01_workbench_optional_variants_1280x900.html`](01_workbench_optional_variants_1280x900.html) | `title="可选变体"`, `pill="暂未生成"`, empty title `"暂未生成变体视频"`, empty body `"你可以先生成主视频，或选择同时生成多个变体。"`, tech note `"本面板不展示完整成片或外部链接；完整成片在交付页面。"` ✓ |

All four runtime-probed strings match Mission §B.3 + approved product decision #2 verbatim.

## Tests

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py \
                    test_matrix_script_workbench_redesign_2026_05_28.py \
                    test_matrix_script_workbench_main_video_result_template.py \
                    test_matrix_script_main_video_result_view.py \
                    test_matrix_script_workbench_production_flow_stepper.py
============================== 68 passed in 0.12s ==============================
```

Broader regression unchanged.

## Explicit no-change statement

This PR does **NOT**: touch any contract, packet, closed enum, schema, endpoint, helper, or wiring; modify Hot Follow / Digital Anchor / Asset Supply files; add provider/model/vendor/engine selectors; fake any media output; add backend generation. The change is **template-only** + tests.

## Remaining backend limitations (unchanged)

No variant generation backend; no final_video worker; closure store volatile. The "暂未生成" pill is the honest state.

## Matrix Script is not production-operable

The wave target after all 4 PRs remains *"UI visually verifiable; backend final-video generation remains pending."*

## Rollback

`git reset --hard <PR-2B-commit>` removes the PR-2C template rewrite + tests + snapshot/report.
