# Matrix Script Delivery Center · Product-Flow Reset · PR-B Implementation Report v1

Date: 2026-05-29
Branch: `reset/ms-delivery-product-flow-cleanup-prb-20260529`
Base: `reset/ms-workbench-product-flow-cleanup-pra-20260529` (PR-A conditionally approved)
Wave: Matrix Script · Product-Flow Reset
Authority: [docs/design/matrix_script_workbench_product_flow_reset_v1.md](../design/matrix_script_workbench_product_flow_reset_v1.md) §6 (Delivery Center reset); user mission `[SYSTEM OVERRIDE]` 2026-05-29 Delivery Center implementer brief.

## 1. Mission

Reframe the Matrix Script Delivery Center as a result + publish surface. Reduce the operator-visible primary scan to six sections + one collapsed diagnostic fold. Retire the prior PR-3 / PR-4 Block A–F structure, the Recovery PR-3 legacy closure block, and the JS-hydrated diagnostic shells from the operator's primary view (preserving every data-role marker inside the diagnostic fold for back-compat).

## 2. Resulting primary IA

The matrix_script branch of [gateway/app/templates/task_publish_hub.html](../../gateway/app/templates/task_publish_hub.html) now renders, in order:

| # | Section | `data-role` anchor | Content |
|---|---|---|---|
| 1 | 交付结果介绍 | `matrix-script-dc-section-intro` | Operator-language paragraph + single result pill (mirrors Workbench Section 1) + next-action line. |
| 2 | 主视频 | `matrix-script-dc-section-main-video` | Preview hero (binds real artifact when present, honest empty state otherwise). No raw `final_video` heading; no fabricated URL. |
| 3 | 必需交付物 | `matrix-script-dc-section-required-deliverables` | Five operator-language rows (字幕 / 音频 / 文案包 / manifest / 交付包) with status + 下载/"在 Workbench 重新生成" CTA. |
| 4 | 可选交付物 | `matrix-script-dc-section-optional-deliverables` | 其他变体 (collapsed fold) + 场景包 + 补充素材. |
| 5 | 发布设置 | `matrix-script-dc-section-publish-settings` | 6-field publish form (platform / account / title / copy / hashtags / scheduled time). Posts to existing closure endpoint with `event_kind=operator_publish`. |
| 6 | 发布回填 | `matrix-script-dc-section-publish-backfill` | Per-variation row with publish URL / publish status / operator note placeholder + metrics-placeholder card. |
| 7 | 技术诊断 (collapsed `<details>`) | `op-console-ms-dc-technical-diagnostics-fold` | Retired PR-3/PR-4 Block A–F op-cards + Recovery PR-3 closure block + pre-existing JS-hydrated diagnostic shells. |

## 3. Files changed

| File | Change |
|---|---|
| [gateway/app/templates/task_publish_hub.html](../../gateway/app/templates/task_publish_hub.html) | Inserted six new PR-B sections + opened the technical-diagnostics outer `<details>` immediately after the `ms_pub.is_matrix_script` gate opens. Closed the outer fold just before the matrix_script branch's closing `{% endif %}`. All legacy PR-3 / PR-4 / Recovery PR-3 markup + the two pre-existing inner JS-diagnostic folds now live inside the new outer fold. |
| [gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py](../../gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py) | **New.** 69 tests covering: 6-section anchor presence + design order, Section 1 paragraph + result pill + first-position, Section 2 preview hero + empty-state copy + no-raw-`final_video`-in-title, Section 3 five fixed kinds + operator labels + "在 Workbench 重新生成" CTA, Section 4 three sub-groups (others fold collapsed by default) + operator '场景包' label (no `scene_pack`), Section 5 six form fields + existing closure endpoint binding + hidden `operator_publish` event_kind + honesty note, Section 6 url/status/note columns + operator-language status words + metrics placeholder, no generation buttons in primary, no production-flow stepper in primary, no task creation controls, forbidden-vocabulary quarantine (9 tokens + raw event_kind enum values + raw 'closure' + provider/model/vendor/engine), no fake video URL / no placeholder player / no fake publish URL, 11 legacy markers preserved inside Section 7 only, Digital Anchor branch byte-isolation. |
| [scripts/render_delivery_center_prb_screenshots.py](../../scripts/render_delivery_center_prb_screenshots.py) | **New.** Jinja2 renderer producing two HTML snapshots against a synthetic empty-state context. |
| [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/01_prb_delivery_center_full_default_collapsed.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/01_prb_delivery_center_full_default_collapsed.html) | **New.** Operator first-scan snapshot — Section 7 collapsed by default. |
| [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/02_prb_delivery_center_full_section7_expanded.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/02_prb_delivery_center_full_section7_expanded.html) | **New.** Architect view — Section 7 expanded. |

No changes to any presenter helper, contract file, schema, packet, runtime, or non-template file (mission item: "minimal presenter/helper copy shaping if required" — turned out to be zero shaping needed; all six sections consume the existing `ms_publish_hub` bundle as already shaped by [publish_hub_render_data.py](../../gateway/app/services/matrix_script/publish_hub_render_data.py)).

## 4. Test results

```
gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py  69 passed (new)
gateway/app/services/tests/test_matrix_script_delivery_center_pr3_reframing.py           PASSED (existing)

PR-A back-compat regression check (re-run on PR-B branch):
gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py        63 passed
gateway/app/services/tests/test_matrix_script_workbench_blocks_a_b_c.py                  PASSED
gateway/app/services/tests/test_matrix_script_workbench_blocks_d_e_f.py                  PASSED
gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py             PASSED
gateway/app/services/tests/test_matrix_script_workbench_template_intact.py               PASSED
gateway/app/services/tests/test_matrix_script_workbench_diagnostics_quarantine.py        PASSED
gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py       PASSED
gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py    PASSED
gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py           PASSED
                                                                                  280 passed total
```

Pre-existing failure (not introduced by PR-B; confirmed failing on the PR-A base):
- `test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` — drift in the prior wave's PR-2D / PR-3 reframing; not in PR-B scope.

## 5. Screenshots

Two rendered HTML snapshots in [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/):

| File | What it shows |
|---|---|
| `01_prb_delivery_center_full_default_collapsed.html` | Sections 1–6 in the primary scan; Section 7 (技术诊断) collapsed (`<details>` without `open`). |
| `02_prb_delivery_center_full_section7_expanded.html` | Same context; Section 7 forced open to verify all legacy data-role markers (`matrix-script-block-a-final-video-primary` … `matrix-script-closure` … `op-console-ms-secondary-shells-fold`) render inside the architect view. |

Both snapshots verify the empty-state path (no media generated yet — the universal state of production today).

## 6. No-change statement (mission boundaries)

This PR makes **no** changes to any of the following:

- No contract changes (`docs/contracts/` untouched).
- No schema changes (`schemas/` untouched).
- No packet changes; no `production_packet*.json` mutation.
- No closed-enum widening (`event_kind` / `publish_status` / `head_reason` / `head_reason_label_zh` / `record_kind` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` unchanged).
- No runtime generation changes; no new endpoint (Section 5's form posts to the existing `POST /api/matrix-script/closures/{task_id}/events` with `event_kind=operator_publish`).
- No Hot Follow touch — Hot Follow publish-hub branch is bytewise unaffected (test `test_prb_section_anchors_scoped_to_matrix_script_branch` asserts all new anchors live before the Digital Anchor branch; Hot Follow has no per-kind gate in this template).
- No Digital Anchor touch — DA branch (`_da_kind == "digital_anchor"`) is bytewise unchanged.
- No Asset Supply touch.
- No fake `final_video` / no fake `publish_url`. Section 2 preview hero either binds a real recommended-variant artifact or shows the operator-language empty state. Section 6 publish-URL column either renders the real `row.publish_url` href or `—`.
- No generation controls in the Delivery Center primary scan (Section 3's missing-row CTA is an `<a>` linking back to `/tasks/{id}/workbench`, never an inline regen button).
- No production-flow stepper in the Delivery Center primary scan.
- No task creation controls.

## 7. Known limitations

1. **Section 3 download buttons are stubs.** The `data-role="ms-dc-section-required-row-download"` buttons render with `title="下载入口在主视频生成能力接入后开放"` but no working href. Real download wiring lands when the artifact retrieval surface ships.
2. **Section 6 metrics placeholder is a static text node.** The `data-role="ms-dc-section-publish-backfill-metrics-placeholder"` element renders `指标投射尚未上线 · 暂不展示数值。` — metrics projection is out of PR-B scope.
3. **Section 6 operator-note column shows `—` for all rows.** The closure helper (`publish_feedback_closure.variation_feedback[]`) does not currently project per-row operator notes; surfacing them when present is a follow-on helper-shape pass (not in PR-B's "no helper shaping" constraint).
4. **The legacy PR-3 publish-settings form lives both in primary (new Section 5) and inside Section 7 (legacy `matrix-script-block-publish-settings`).** Both forms post to the same closure endpoint with the same shape; submitting one and then the other would record two events. The legacy form is inside the collapsed fold by default, so this is an architect-only edge case.
5. **Section 6 status pills are operator-language text only, not info-pill chips.** The legacy `<span class="info-pill ms-result-status__kind ms-result-status__kind--…">` styling is preserved inside Section 7 for tests that assert the old visual; Section 6 uses plain operator-language text for the four states (`已发布` / `失败` / `已撤回` / `待发布`). This is per design §6 row 6 ("operator-language rows" — no fixed pill style required).
6. **The architect Section 7 contains TWO nested `<details>` (`op-console-ms-secondary-shells-fold`, `op-console-ms-delivery-comprehension-fold`).** Operator clicks the outer Section 7 to reveal the legacy A–F op-cards; the two inner folds remain individually collapsed.

## 8. Verdict request

Requesting reviewer verdict on:

1. The six-section operator IA matches design §6 exactly.
2. The seven-block legacy structure (header + A–F + Recovery PR-3 closure + JS-hydrated shells) is correctly quarantined behind the `op-console-ms-dc-technical-diagnostics-fold` `<details>`.
3. The publish-settings form (Section 5) correctly reuses the existing closure endpoint with no enum widening.
4. The 69-test PR-B suite + the 280-test combined PR-A+PR-B regression run cover the design §6 acceptance bar adequately for a presentation-layer reset.
5. Confirmation that PR-C (real-browser visual validation per design §8) should open next after this PR-B is reviewed.

Stop here. Do not start PR-C until PR-B is reviewed per design §8 sequencing rule.
