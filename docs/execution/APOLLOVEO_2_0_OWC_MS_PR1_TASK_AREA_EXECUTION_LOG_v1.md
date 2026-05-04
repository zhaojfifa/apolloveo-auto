# ApolloVeo 2.0 · OWC-MS PR-1 — Matrix Script Task Area Workflow Convergence — Execution Log v1

Date: 2026-05-04
Status: Engineering complete on branch `claude/owc-ms-pr1-task-area-convergence`; PR opening pending.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC), Phase OWC-MS.
Phase Gate: [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md).
Predecessors: OWC authority/gate normalization PR (#121, squash commit `27aa950`); Operator Capability Recovery PR-1..PR-4 (all merged 2026-05-04).

## 1. Scope

OWC-MS PR-1 is the first of three implementation PRs in the Operator Workflow Convergence Wave for Matrix Script. It lands the OWC-MS gate spec §3 Task Area scope:

- **MS-W1 — Task Area three-tier projection** (脚本任务 → 变体任务 → 发布任务). Projection over the existing Matrix Script packet + `line_specific_refs[matrix_script_variation_matrix].delta.cells[]` + closure `variation_feedback[]` rows + `channel_metrics[]`. No packet schema change; no closure shape change.
- **MS-W2 — Task Area state vocabulary + 8-field card**. Eight operator-language stages (`已创建 / 待配置 / 生成中 / 待校对 / 成片完成 / 可发布 / 已回填 / 已归档`) projected from L1 step status / L2 artifact facts / L3 current attempt / L4 ready gate + closure publish events. Eight-field operator-language card body (主题 / 核心脚本名称 / 当前变体数 / 可发布版本数 / 已发布账号数 / 当前最佳版本 / 最近一次生成时间 / 当前阻塞项).

Out of scope (carried by OWC-MS PR-2 / PR-3 + OWC-DA + later phases):
- Workbench five-panel convergence (MS-W3..W6) — OWC-MS PR-2.
- Delivery copy_bundle exposure + 回填 multi-channel rendering (MS-W7 + MS-W8) — OWC-MS PR-3.
- "当前最佳版本" operator selector — OWC-MS PR-2 (workbench D 校对区 with additive `review_zone` enum on `operator_note` events).
- Digital Anchor surface convergence — OWC-DA.
- Hot Follow modifications — out of all OWC scope (Hot Follow baseline byte-isolated).

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md` (with §13 Product-Flow Module Presence)
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 OWC wave authority
- `docs/reviews/owc_ms_gate_spec_v1.md` §3 (MS-W1 + MS-W2 binding scope)
- `docs/reviews/owc_da_gate_spec_v1.md` (read-only — predecessor pattern reference for OWC-DA, NOT touched by this PR)
- `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`

### 2.3 Line-specific execution authority (binding)
- `docs/product/matrix_script_product_flow_v1.md` §§5.1 (三层任务) / §5.2 (八操作语言状态) / §5.3 (任务卡片字段)

### 2.4 Factory-wide / surface authority (read-only)
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`

### 2.5 Existing code surfaces consumed
- `gateway/app/services/matrix_script/task_card_summary.py` (PR-U1 — existing helper composed verbatim; no mutation)
- `gateway/app/services/matrix_script/closure_binding.py` (PR-3 — read-only via `get_closure_view_for_task`)
- `gateway/app/services/matrix_script/publish_feedback_closure.py` (Phase D.0 closure shape; read-only consumer)
- `gateway/app/services/operator_visible_surfaces/projections.py` (`build_board_row_projection` — existing wiring; not modified)
- `gateway/app/services/task_router_presenters.py::build_tasks_page_rows` (cross-cutting wiring seam; matrix_script branch only)
- `gateway/app/templates/tasks.html` (matrix_script-gated `{% if line_id == "matrix_script" and ms_summary.is_matrix_script %}` block)

### 2.6 Conflicts found
- **PR-U1 publishable_variation_count was hardcoded to None via `PUBLISHABLE_COUNT_GATED_BY_D1`.** That gating reflected Plan E phase scope where the unified `publish_readiness` producer was forbidden. Operator Capability Recovery PR-1 (#114) landed the unified producer + closure-binding wiring; the gating sentinel is no longer truthful for OWC. Resolution: OWC-MS PR-1 rebinds `publishable_variation_count_value` to the closure-derived count of `variation_feedback[]` rows where `publish_status == "published"`. The PR-U1 helper itself is preserved bytewise; the rebind happens in the new `derive_matrix_script_full_card_summary` wrapper that supersets PR-U1.

## 3. Files Changed

### New files
- `gateway/app/services/matrix_script/task_area_convergence.py` — projection module exposing `derive_matrix_script_eight_stage_state`, `derive_matrix_script_three_tier_lanes`, `derive_matrix_script_full_card_summary`, and `derive_matrix_script_full_card_summary_for_task`. Read-only over row + closure view; no mutation; no contract / packet / schema change. Closes the eight stages and the three lanes against the existing four-layer state and closure shape.
- `gateway/app/services/tests/test_matrix_script_task_area_convergence.py` — 37 import-light test cases covering: (i) 8-stage constant authority parity with product-flow §5.2 labels; (ii) 8 stage projections (one per stage incl. archived precedence over backfilled and backfilled precedence over publishable); (iii) `stage_index` ordering invariant; (iv) non-matrix_script row isolation for the eight-stage projection; (v) three-tier lanes structural invariants (lane order, lane labels, script lane subject + ref carry-through); (vi) variation lane cell-to-feedback join with and without closure; (vii) publish lane multi-channel flatten (incl. dedup of `platform` across variations); (viii) full card summary PR-U1 key preservation (15 keys); (ix) publishable_variation_count rebind from closure published count (zero / one / no-closure cases); (x) core_script_name read from `source_script_ref` ; (xi) published_channel_count dedup across variations; (xii) best_version intentional-None + tooltip; (xiii) last_generated_at preference order (`updated_at` → `last_generated_at` → `created_at`); (xiv) eight-stage and three-tier lanes attached on the summary; (xv) Hot Follow / Digital Anchor row isolation; (xvi) closure non-mutation invariant; (xvii) row non-mutation invariant; (xviii) no vendor / model / provider / engine / swiftcraft identifier in summary repr; (xix) lane-row count invariant; (xx) missing-kind row collapses to `{}`.
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR1_TASK_AREA_EXECUTION_LOG_v1.md` — this file.

### Modified files
- `gateway/app/services/task_router_presenters.py` — extended the existing `kind_value == "matrix_script"` branch in `build_tasks_page_rows` (no new branch). Added the import for `derive_matrix_script_full_card_summary_for_task`; attached additional row keys (`packet`, `updated_at`, `last_generated_at`, `archived`, `final`) needed by the new projections; the `matrix_script_card_summary` PR-U1 attachment is preserved verbatim and a new `matrix_script_task_area_convergence` key carries the OWC-MS superset (read-only via `get_closure_view_for_task`; never lazy-creates a closure on the in-process store).
- `gateway/app/templates/tasks.html` — extended the existing `{% if line_id == "matrix_script" and ms_summary.is_matrix_script %}` block (no new branch). Added: (i) eight-stage badge above the existing tri-state badge in `task-card__right`; (ii) four new operator-language fields in a second `task-card__meta` row (`ms-field-row-owc`); (iii) three-tier lanes summary block (lane label + count). All template additions sit inside the existing matrix_script branch; the `{% else %}` branch (Hot Follow / Digital Anchor / baseline) is bytewise unchanged. The PR-U1 template spans (`ms-subject-label`, `ms-subject-value`, `ms-current-variation`, `ms-publishable-variation`, `ms-current-blocker`, `operator-bucket`, `ms-action-workbench`, `ms-action-delivery`) all render with their PR-U1 markup; only the `ms-publishable-variation` value source switches from PR-U1's gated-by-D1 sentinel rendering to the OWC-derived count when `ms_owc` is present.

### NOT modified
- Hot Follow source files (any path containing `hot_follow`).
- Digital Anchor source files (any path under `gateway/app/services/digital_anchor/`).
- Asset Supply files (`gateway/app/services/asset/*`).
- Any contract under `docs/contracts/`.
- Any sample under `schemas/`.
- Any worker / runtime / capability-adapter file.
- Workbench template (`task_workbench.html`) — out of scope for PR-1 (MS-W3..W6 land in OWC-MS PR-2).
- Publish hub template (`task_publish_hub.html`) — out of scope for PR-1 (MS-W7 + MS-W8 land in OWC-MS PR-3).
- `gateway/app/services/matrix_script/task_card_summary.py` — PR-U1 helper preserved bytewise.
- `gateway/app/services/matrix_script/publish_feedback_closure.py` — closure shape preserved.
- `gateway/app/services/matrix_script/closure_binding.py` — closure binding preserved.

## 4. Why scope is minimal and isolated

- One new service module (projection only — composed over the PR-U1 helper plus a read-only closure view).
- One new dedicated test module.
- Two existing seams modified: `task_router_presenters.build_tasks_page_rows` (matrix_script branch only) and `tasks.html` (matrix_script-gated block only).
- No packet truth, validator rule, schema, sample, contract, or template-truth mutation outside the rebind of `publishable_variation_count_value` from the gated-by-D1 sentinel to the closure-derived count. No closure write through this PR; the projection reads the closure read-only via `get_closure_view_for_task`.
- No Digital Anchor / Hot Follow business behavior change; no Asset Supply expansion.
- No durable persistence — projection reads the in-process store per Recovery red lines.
- No provider / model / vendor / engine identifier admitted into any payload (boundary tested).

## 5. Tests Run

Local Python 3.9.6 (the unrelated `gateway/app/config.py` PEP 604 collection issue on `str | None` Field defaults remains a pre-existing repo baseline issue documented in PR-1 / PR-2 / PR-3 / PR-4 logs; affected files: `test_matrix_script_phase_b_authoring.py`, `test_matrix_script_source_script_ref_shape.py`, `test_matrix_script_workbench_dispatch.py`, `test_new_tasks_surface.py`. Confirmed pre-existing on `main` via `git stash` + re-run; not caused by this PR).

OWC-MS PR-1 dedicated test module:
- `test_matrix_script_task_area_convergence.py` — **37/37 PASS**.

Adjacent regression (no behavior change expected; verifies byte-isolation):
- `test_matrix_script_task_card_summary.py` — PASS (PR-U1 helper preserved bytewise; the PR-U1 test surface is untouched)
- `test_matrix_script_b4_artifact_lookup.py` — PASS
- `test_matrix_script_delivery_zoning.py` — PASS
- `test_matrix_script_delivery_comprehension.py` — PASS
- `test_matrix_script_workbench_comprehension.py` — PASS
- `test_matrix_script_closure_binding.py` — PASS
- `test_matrix_script_closure_publish_hub_wiring.py` — PASS
- `test_matrix_script_closure_surface_boundary.py` — PASS
- `test_matrix_script_f2_minting_flow.py` — PASS
- `test_digital_anchor_create_entry.py` — PASS
- `test_digital_anchor_closure_binding.py` — PASS
- `test_digital_anchor_workspace_wiring.py` — PASS
- `test_digital_anchor_surface_boundary.py` — PASS
- `test_publish_readiness_unified_producer.py` — PASS
- `test_publish_readiness_surface_alignment.py` — PASS
- `test_final_provenance_emission.py` — PASS
- `test_asset_library_read_only.py` — PASS
- `test_asset_promote_lifecycle.py` — PASS
- `test_asset_surface_boundary.py` — PASS

**Aggregate: 364 PASS / 0 FAIL** on Python 3.9 import-light set (37 new + 327 adjacent).

## 6. Acceptance Mapping (against `owc_ms_gate_spec_v1.md` §3 + §6)

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| MS-W1 — Task Area three-tier projection visible on `tasks.html` matrix_script branch | PASS | `derive_matrix_script_three_tier_lanes` + new `data-role="ms-three-tier-lanes"` block; tests `test_three_tier_lanes_returns_all_three_lanes_in_order`, `test_script_lane_carries_subject_and_source_script_ref`, `test_variation_lane_renders_one_row_per_cell_with_pending_default`, `test_variation_lane_joins_closure_publish_status_when_present`, `test_publish_lane_flattens_channel_metrics_per_variation_per_channel` |
| MS-W2 — Task Area eight-stage operator-language state on `tasks.html` matrix_script branch | PASS | `derive_matrix_script_eight_stage_state` + new `data-role="ms-eight-stage"` badge; tests `test_eight_stages_constant_matches_product_flow_authority` + 7 per-stage projection tests + `test_stage_archived_takes_precedence_over_other_signals` + `test_eight_stage_state_resolves_publishable_under_published_closure` |
| MS-W2 — eight-field card (主题 / 核心脚本名称 / 当前变体数 / 可发布版本数 / 已发布账号数 / 当前最佳版本 / 最近一次生成时间 / 当前阻塞项) on `tasks.html` matrix_script branch | PASS | `derive_matrix_script_full_card_summary` superset of PR-U1; tests `test_full_summary_preserves_pr_u1_keys` (15 PR-U1 keys preserved), `test_full_summary_core_script_name_reads_source_script_ref`, `test_full_summary_published_channel_count_dedupes_across_variations`, `test_full_summary_best_version_intentionally_none_for_pr1`, `test_full_summary_last_generated_at_prefers_updated_at`, `test_full_summary_last_generated_at_falls_back_to_created_at`; template renders new fields in `data-role="ms-field-row-owc"` |
| publishable_variation_count rebound from D1-gated sentinel to closure-derived count | PASS | `test_full_summary_rebinds_publishable_variation_count_to_closure_published_count`, `test_full_summary_publishable_count_zero_when_no_closure` |
| Hot Follow byte-isolation | PASS | No file under `gateway/app/services/hot_follow*` or template `hot_follow_*.html` modified; existing `{% else %}` branch in `tasks.html` unchanged; `test_full_summary_returns_empty_for_hot_follow_row` asserts behavioral isolation |
| Digital Anchor byte-isolation | PASS | No file under `gateway/app/services/digital_anchor/*` modified; `test_full_summary_returns_empty_for_digital_anchor_row` asserts behavioral isolation |
| Asset Supply consumed read-only | n/a | No Asset Supply file touched (PR-1 does not consume Asset Supply) |
| No PR-1 / PR-2 / PR-3 / PR-4 truth modified | PASS | Forbidden-scope audit §7 below |
| Product-Flow Module Presence rule (ENGINEERING_RULES §13) — modules visible on `tasks.html` | PASS | Reviewer can read `gateway/app/templates/tasks.html` matrix_script branch and confirm: 8-stage badge (`data-role="ms-eight-stage"`), 8-field card (`data-role="ms-field-row"` + `data-role="ms-field-row-owc"`), three-tier lanes (`data-role="ms-three-tier-lanes"`) |
| Test floor ≥25 cases per gate spec §5.2 | PASS | 37 test cases shipped in `test_matrix_script_task_area_convergence.py` |

## 7. Forbidden-Scope Audit (against `owc_ms_gate_spec_v1.md` §4)

### §4.1 Truth-source / contract preservation
| Red line | Status |
| --- | --- |
| No Matrix Script packet truth mutation | clean — no packet schema or sample modified |
| No reopen of §8.A–§8.H correction chain | clean — no §8 artifact touched |
| No widening of `target_language`, canonical axes, or `source_script_ref` accepted-scheme set | clean — no scheme set or axis set modified |
| No operator-driven Phase B authoring (variation cells stay deterministically derived) | clean — projection-only; no cell mutation |
| No `source_script_ref` repurposing | clean — projection reads the bare ref string for display only; no dereference |
| No new authoritative truth source for publishability | clean — `publishable_variation_count_value` rebound to closure-derived count consumes the existing PR-3 closure shape; PR-1 unified producer remains the only `publishable` truth source |
| No second producer for `final_provenance` (L3) or L4 advisory | clean — neither is touched by this PR |

### §4.2 Cross-line preservation
| Red line | Status |
| --- | --- |
| No Hot Follow file touched | clean |
| No Digital Anchor file touched | clean |
| No cross-cutting wiring change outside the existing `panel_kind == "matrix_script"` / `_ms_kind == "matrix_script"` branches | clean — `task_router_presenters.py` edit confined to existing matrix_script branch; `tasks.html` edit confined to existing `{% if line_id == "matrix_script" and ms_summary.is_matrix_script %}` block |

### §4.3 Wave-position preservation
| Red line | Status |
| --- | --- |
| No Platform Runtime Assembly Phases A–E | clean |
| No Capability Expansion W2.2 / W2.3 / durable persistence / runtime API / third production line | clean |
| No Plan A live-trial reopen | clean — no Plan A artifact modified |
| No new operator-eligible discovery surface promotion | clean |

### §4.4 Scope-boundary preservation
| Red line | Status |
| --- | --- |
| No provider / model / vendor / engine controls or operator selector | clean — boundary tested via `test_full_summary_carries_no_provider_or_vendor_identifier` |
| No donor namespace import | clean — no `from swiftcraft.*` |
| No Asset Supply page / promote service / DAM expansion | clean |
| No React / Vite full rebuild or new component framework | clean — Jinja2 + minimal data-role attributes only |
| No durable persistence backend swap | clean — closure store remains in-process |
| No bundling of MS-W* slices | clean — only MS-W1 + MS-W2 land here; MS-W3..W8 deferred |

### §4.5 Closeout-paperwork independence
| Red line | Status |
| --- | --- |
| No forced advancement of prior closeout signoffs (recovery PR-1..PR-4 closeouts, Plan E phase closeouts) | clean — none touched |

## 8. Residual Risks

- **In-process closure store** persistence: when the gateway process restarts, `variation_feedback[]` rows reset to `publish_status == "pending"` for all closures. The OWC-MS PR-1 task-area projection therefore renders zero-published immediately after restart. Acceptable per Recovery Decision §4.3 (minimum operator capability, not durable persistence). A later wave may swap the in-process store for a durable backend without changing the closure shape or the projection.
- **`compose_status` enum is read-as-string**: the eight-stage projection treats `"running"`, `"in_progress"`, and `"queued"` as 生成中 stage. If a downstream Hot Follow evolution introduces additional running-state tokens, they will fall through to either 待校对 (if `compose_ready=True`) or 已创建 (otherwise). No silent failure; just a temporarily lower-fidelity stage label until the projection is extended.
- **`source_script_ref` rendering is the bare ref string**: 核心脚本名称 currently shows `content://matrix-script/source/<token>`, which is operator-readable but not human-friendly. A human-readable display name (e.g. derived from the `source_script_ref` token's resolved metadata) would require dereferencing the ref, which is gated to a future wave (Plan E F2 minting flow exposes the ref construction; F3 dereference is a future capability). The bare ref display is consistent with the existing operator brief §0.2 product-meaning of `source_script_ref` and is operator-readable.
- **当前最佳版本 stays None / —**: this is intentional per gate spec §3 MS-W2 + §4.1 (no operator-driven Phase B authoring; best-version selection is OWC-MS PR-2 workbench D 校对区 scope). The tooltip names the gating in operator language.
- **Variation lane shows 0 rows for tasks with empty `line_specific_refs`**: the projection is correct (no cells = no variation rows), but operators may interpret the empty lane as "task is broken." The 8-stage badge surfaces 待配置 in this case to give operator context. Future copy refinement may add an explicit empty-state hint inside the lane block.
- **`channel_metrics[].account_id` and `published_at` field names are not yet in the closed Phase D.0 contract**: today's closure shape exposes `channel_metrics[]` with the four numeric fields (`impressions`, `views`, `engagement_rate`, `completion_rate`) plus a `platform` enum. The publish lane projection therefore reads `account_id` and `published_at` defensively (returns `None` when missing). When OWC-MS PR-3 lands the multi-channel 回填 rendering it will need to resolve where these per-publish fields live; today's projection is forward-compatible (returns `None` rather than crashing).

## 9. Exact Statement of What Remains for the Next PR

OWC-MS PR-2 — Matrix Script Workbench Five-Panel Convergence (MS-W3 + MS-W4 + MS-W5 + MS-W6) per `owc_ms_gate_spec_v1.md` §5. PR-2 may not start until this PR-1 is merged and reviewed. Claude stops after this PR-1 is opened.

## 10. References

- Gate spec: `docs/reviews/owc_ms_gate_spec_v1.md`
- Sister-phase gate spec: `docs/reviews/owc_da_gate_spec_v1.md`
- Predecessor docs PR: `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`
- Engineering rule binding: `ENGINEERING_RULES.md` §13 Product-Flow Module Presence
- Line-specific authority: `docs/product/matrix_script_product_flow_v1.md`
- Recovery PR-1 (publish_readiness producer): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`
- Recovery PR-3 (Matrix Script closure binding): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md`
- PR-U1 (Plan E Matrix Script Task Area comprehension): `docs/execution/PLAN_E_MATRIX_SCRIPT_UI_U1_TASK_AREA_COMPREHENSION_EXECUTION_LOG_v1.md`
