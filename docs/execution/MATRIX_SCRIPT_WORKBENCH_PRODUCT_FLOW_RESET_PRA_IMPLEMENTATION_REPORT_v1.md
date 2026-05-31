# Matrix Script Workbench · Product-Flow Reset · PR-A Implementation Report v1

Date: 2026-05-29
Branch: `reset/ms-workbench-product-flow-cleanup-pra-20260529`
Base: `origin/design/ms-workbench-product-flow-reset-20260529` (fc9cdf4, which itself sits on top of `origin/VeoMatrixVoice01`)
Wave: Matrix Script Workbench · Product-Flow Reset
Authority: [docs/design/matrix_script_workbench_product_flow_reset_v1.md](../design/matrix_script_workbench_product_flow_reset_v1.md) §4 (target IA), §5 (forbidden vocab), §8 PR-A scope, §9 acceptance.

## 1. Mission

Subtractive IA cleanup of the Matrix Script Workbench primary view. Retire the additive PR-2A → PR-2D / OWC-MS-RO PR-2 / PR-3 legacy A/B/C/D/E/F op-cards from the operator's primary scan; reduce the surface to exactly four primary sections + one collapsed diagnostic fold. Preserve all retired `data-role` markers inside the diagnostic fold for back-compat with prior structural tests.

## 2. Resulting primary IA

The matrix_script branch of [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) now renders, in order:

| # | Section | `data-role` anchor | Source |
|---|---|---|---|
| 1 | 主视频结果 (dominant first screen) | `matrix-script-main-video-result` | unchanged (PR-2A helper) |
| 2 | 生产流程可观测 (compact stepper + inline `<details>` per step) | `matrix-script-production-flow-stepper` | rewritten (PR-A) |
| 3 | 可选变体 (compact: 主推 + 其他变体 fold) | `matrix-script-section-optional-variants` | new (PR-A) |
| 4 | 交付入口 (lightweight: 2-line + CTA) | `matrix-script-section-delivery-entry` | new (PR-A) |
| 5 | 技术诊断 (collapsed `<details>`) | `op-console-ms-technical-diagnostics-fold` | new outer fold (PR-A) |

Section 5 contains:
- The retired legacy Block A / B / C / D / E / F op-cards (preserved verbatim — only their visual prominence is demoted).
- The pre-existing PR-U2 / MS-W3 / Variation Panel / RC PR-2..PR-4 secondary diagnostics fold (now nested inside the outer Section 5 fold).

## 3. Files touched

| File | Change |
|---|---|
| [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) | Replaced PR-2B anchor stepper with inline-expandable stepper (§ Section 2). Inserted new Section 3 (`matrix-script-section-optional-variants`) and Section 4 (`matrix-script-section-delivery-entry`). Wrapped the legacy A–F op-cards inside a new outer `<details data-role="op-console-ms-technical-diagnostics-fold">` (Section 5, collapsed by default). Closed the outer fold before the matrix_script gate's `{% endif %}`. |
| [gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py](../../gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py) | Updated `test_stepper_carries_redesign_wave_attribute` to assert the new PR-A wave marker (`2026-05-29-pra`) in place of the retired PR-2B marker. |
| [gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py](../../gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py) | **New.** 63 tests covering: 4-section presence + design ordering, Section 1 dominance, inline-expandable stepper shape (3 step details), Section 3 compactness + empty-state copy + no-table / no-candidate-card audit, Section 4 lightweight (no rows / no forms / no tables / no publish-feedback), §5 forbidden-vocabulary quarantine (12 parametrized tokens + provider/model/vendor/engine + task ID heading), no-fake-media (no `.mp4` / `.m3u8` / `<video>` / `<iframe>` / raw `final_video` field), legacy block markers inside Section 5 only (6 parametrized), legacy block heading text retired from primary, Section 5 collapsed by default, anchor-question coverage, per-section anchor presence, Hot Follow / Digital Anchor byte-isolation. |
| [scripts/render_workbench_pra_screenshots.py](../../scripts/render_workbench_pra_screenshots.py) | **New.** Jinja2-only renderer producing two HTML snapshots of the matrix_script workbench in the empty-state (no-media) universal state — one with Section 5 collapsed (operator scan), one with Section 5 expanded (architect view). |
| [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/01_pra_workbench_full_default_collapsed.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/01_pra_workbench_full_default_collapsed.html) | **New.** Rendered HTML snapshot — operator first-screen (Section 5 collapsed). |
| [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/02_pra_workbench_full_section5_expanded.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/02_pra_workbench_full_section5_expanded.html) | **New.** Rendered HTML snapshot — architect view (Section 5 expanded). |

## 4. Test results

```
gateway/app/services/tests/test_matrix_script_workbench_blocks_a_b_c.py       PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_blocks_d_e_f.py       PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py  PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_template_intact.py    PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_diagnostics_quarantine.py PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py PASSED (updated)
gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py PASSED (existing)
gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py PASSED (63 new tests)
                                                                          270 passed
```

Pre-existing unrelated failures (not caused by PR-A; failing on the design branch base too):
- `test_operator_console_ui_rebuild.py::test_matrix_script_workbench_uses_operator_language_block_titles` — asserts legacy block titles like `变体策略` / `生成 / 重新生成` / `候选评审` / `交付概览` that were renamed by PR-2C / PR-2D before this branch.
- `test_operator_console_ui_rebuild.py::test_delivery_center_block_titles_use_operator_language` — analogous Delivery Center title drift in a prior wave.

These are out of PR-A scope (Delivery Center reset is PR-B per design §8).

## 5. Acceptance bar self-check (design §9)

| # | Criterion | PR-A status |
|---|---|---|
| 1 | First-screen dominance of 主视频结果 | ✅ Section 1 is the first `op-card` after the matrix_script gate (`test_section1_is_first_op_card_in_branch`). |
| 2 | Task metadata not primary | ✅ Block A goal-summary card retired to Section 5; no task-meta heading inside Sections 1–4 (`test_task_id_not_a_heading_in_primary`). |
| 3 | Compact stepper only; no legacy A/B/C/D/E/F primary visible | ✅ `test_legacy_block_marker_inside_section5_only` (parametrized × 6) + `test_legacy_block_*_visible_title_not_in_primary`. |
| 4 | Section 3 empty state = one operator message | ✅ Verbatim Mission §B.3 copy (`test_section3_empty_state_uses_design_verbatim_copy`); no per-candidate cards (`test_section3_does_not_render_four_empty_candidate_cards`). |
| 5 | Section 4 = 2-line + CTA, no rows / form / table | ✅ `test_section4_contains_no_deliverable_rows` (audits `<form>`, `<table>`, `ms-block-f-required-row`, `ms-block-f-optional-row`, `publish-feedback`). |
| 6 | Delivery + publishing only in Delivery Center | ✅ Section 4 CTA points to `/tasks/{{task_id}}/publish`; no publish action lives in the workbench. (Delivery Center itself is PR-B.) |
| 7 | §5 forbidden vocabulary quarantined from primary | ✅ `test_forbidden_token_not_in_primary_slice` parametrized over 12 tokens, comments stripped; `test_no_provider_model_vendor_engine_selector_in_primary` covers R3. |
| 8 | Section 5 `<details>` collapsed by default | ✅ `test_section5_details_collapsed_by_default`. |
| 9 | No fake video output | ✅ `test_no_fake_video_url_in_primary` + `test_no_placeholder_video_player_in_primary` + `test_no_raw_final_video_field_in_primary`. |
| 10 | No provider/model/vendor/engine selector | ✅ As above. |
| 11 | Operator answers 5 anchor questions from Section 1 + 2 only | ✅ `test_anchor_questions_answered_in_section1_and_section2`. |
| 12 | Per-section `data-role` anchor in matrix_script branch | ✅ `test_each_section_has_data_role_anchor` parametrized × 5. |

A full visual validation against a real browser is the explicit scope of **PR-C**; the rendered HTML snapshots above are best-effort offline previews against a synthetic empty-state context.

## 6. Hard non-goals — explicit no-change statement

This PR makes **no** changes to any of the following:

- No contract changes (`docs/contracts/` untouched).
- No schema changes (`schemas/` untouched).
- No packet changes; no `production_packet*.json` mutation.
- No closed-enum widening (`status_code` / `head_reason` / `package_status_kind` / `event_kind` / `review_zone` / `recommended_bucket` unchanged).
- No runtime generation changes; no new endpoint; no closure event mutation.
- No Hot Follow touch (`gateway/app/services/hot_follow/*` untouched; Hot Follow workbench branch unchanged).
- No Digital Anchor touch (matrix_script gate is bytewise isolated from `panel_kind == "digital_anchor"` branch — see `test_pra_changes_scoped_to_matrix_script_branch`).
- No Asset Supply touch.
- No fake `final_video`; the Section 1 preview hero either binds a real artifact via the existing helper or renders the honest empty-state copy.
- Matrix Script remains **not production-operable**. Backend final-video generation is still pending the Capability Expansion Wave. PR-A is a subtractive UI cleanup that makes the operator surface honestly reflect that fact — it does not advance generation, publishing, or any state-transition capability.

## 7. Boundary preserved

- Section 1 helpers (`derive_matrix_script_main_video_result`), Section 2 expandable detail helpers (`script_structure_view`, `readable_variant_view`, `recommended_action_view`), Section 3 helpers (`preview_compare_view`, `recommended_action_view`), Section 4 (`ops_pr.publishable`) are all unchanged in shape — PR-A is template-only.
- All seven existing matrix_script presenter helpers continue to be the sole producers of their respective surface data. No new helper module introduced.
- All retired legacy block `data-role` markers (`matrix-script-block-a-goal-summary` … `matrix-script-block-f-delivery-teaser` and their per-row children) survive inside Section 5 — back-compat with the prior wave's 147 structural tests is preserved.

## 8. Next steps

Stop here. Do not start PR-B (Delivery Center product-flow cleanup) until PR-A is reviewed per design §8 sequencing rule.

Reviewers should focus on:
1. Confirming the four primary sections render correctly under each real task state (current_fresh main video / generating / awaiting_review / not_generated empty state). The PR-A test suite covers source-level shape; live visual validation is PR-C.
2. Confirming no Section 5 helper / diagnostic surface regressed inside the now-nested fold (PR-U2 / MS-W3 / Variation Panel / RC PR-2..PR-4 evidence indexes).
3. Confirming Hot Follow + Digital Anchor branches are bytewise unaffected.
