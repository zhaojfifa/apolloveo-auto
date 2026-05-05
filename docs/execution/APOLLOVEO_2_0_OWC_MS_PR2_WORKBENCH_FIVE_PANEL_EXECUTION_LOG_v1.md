# ApolloVeo 2.0 · OWC-MS PR-2 — Matrix Script Workbench Five-Panel Convergence — Execution Log v1

Date: 2026-05-05
Status: Engineering complete on branch `claude/owc-ms-pr1-task-area-convergence` (re-used per branch-strategy convergence on the OWC-MS line); PR opening pending.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC), Phase OWC-MS.
Phase Gate: [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md).
Predecessors: OWC authority/gate normalization PR (#121, squash commit `27aa950`); OWC-MS PR-1 (Task Area Workflow Convergence — `8862adc` + post-merge corrections `cdc6cb1` and `7569f0e`); Operator Capability Recovery PR-1..PR-4 (all merged 2026-05-04).

## 1. Scope

OWC-MS PR-2 is the second of three implementation PRs in the Operator Workflow Convergence Wave for Matrix Script. It lands the OWC-MS gate spec §3 Workbench five-panel scope **for the four panels in the binding-and-exhaustive set**:

- **MS-W3 — Workbench A 脚本结构区 (read-view)**. Operator-language read-view of 标题 / Hook / Body / CTA / 关键词 / 禁用词 derived from the closed `task["config"]["entry"]` payload. `source_script_ref` is rendered verbatim as an opaque-by-construction handle; **never dereferenced**. Sections and taxonomies whose body text/values are not yet on the contract surface render the `unauthored_pending_outline_contract` sentinel with operator-language explanation pointing at the future Outline Contract per matrix_script_product_flow §9.2. The panel asserts the `phase_b_authoring_forbidden` notice citing OWC-MS gate spec §4.1.
- **MS-W4 — Workbench C 预览对比区**. Per-variation rows from `matrix_script_workbench_variation_surface_v1.variation_plan.cells` joined with `copy_bundle.slots`. Each row carries `axis_selections / script_slot_ref / slot_body_ref / slot_length_hint / language_scope`. `preview_status` reads from the existing `matrix_script_delivery_binding_v1` `variation_manifest` row's `artifact_lookup` (Plan E B4 contract). `publish_status` reads the Recovery PR-3 closure `variation_feedback[]` row read-only. `recommended_version` derives strictly from PR-1 unified `publish_readiness.publishable + head_reason` (single producer; no second truth source). `diff_hints` is a per-axis distinct-value comparator over cells.
- **MS-W5 — Workbench D 校对区**. Four review zones (字幕 / 配音 / 文案 / CTA) writing through the existing Recovery PR-3 closure event endpoint with the additive `review_zone` field. **The single contract touch in PR-2** is the additive `REVIEW_ZONE_VALUES = {"subtitle", "dub", "copy", "cta"}` enum on the `operator_note` event payload (gate spec §3 MS-W5: "an enum closed-set extension on event payload is the only contract touch"). The closure-shape envelope, the `variation_feedback[]` row shape, the closed `EVENT_KINDS` set, and `ACTOR_KINDS` are all unchanged. The `review_zone` value is recorded as an optional key on the appended `feedback_closure_records[]` entry only.
- **MS-W6 — Workbench E 质检与诊断区**. Operator-language ready-gate explanation derived from PR-1 unified `publish_readiness` (closed `head_reason` enum + `consumed_inputs.first_blocking_reason`). `risk_items` mirror `publish_readiness.blocking_advisories[]` verbatim — no new advisory id / hint / evidence_field. `compliance_items` enumerate the operator-visible surface red lines (no provider/model/vendor/engine controls; no Phase B authoring). `quality_items` always emit three rows (时长 / 清晰度 / 字幕可读性) — duration observed from `slot.length_hint`, the other two render the `unobservable_pending_upstream` sentinel naming the gate. `artifact_status_items` flatten the existing `delivery_comprehension` lanes into operator-language rows. `publish_blocking_explanation` is the same shape Delivery Center emits — cross-surface consistency.

Out of scope (carried by OWC-MS PR-3 + OWC-DA + later phases):

- Delivery Center copy_bundle exposure (MS-W7) — OWC-MS PR-3.
- Delivery 回填 multi-channel rendering (MS-W8) — OWC-MS PR-3.
- Per-variation artifact provenance — gated by future Plan E variation-level provenance work; today's variation_manifest row carries one shared `artifact_lookup` and the comprehension layer surfaces the granularity gap.
- 当前最佳版本 operator selector — the `recommended_version` marker buckets variations into `publishable_candidate / blocked_pending_publish_readiness / undetermined_pending_review`; no operator selection / pinning happens at this layer.
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
- `docs/reviews/owc_ms_gate_spec_v1.md` §3 (MS-W3 + MS-W4 + MS-W5 + MS-W6 binding scope), §4 (forbidden scope), §5.1 (per-PR file isolation), §5.2 (≥40 test floor), §6 (MS-A1..MS-A8 evidence), §7 (preserved freezes), §8 (stop conditions), §9 (R1..R5 review)
- `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR1_TASK_AREA_EXECUTION_LOG_v1.md`

### 2.3 Line-specific execution authority (binding)
- `docs/product/matrix_script_product_flow_v1.md` §6.1A (Workbench A) / §6.1C (Workbench C) / §6.1D (Workbench D) / §6.1E (Workbench E)

### 2.4 Factory-wide / surface authority (read-only)
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md` §5.3 Workbench (Matrix Script block)

### 2.5 Existing code surfaces consumed (not mutated)
- `gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench` — extended only inside the existing `panel_kind == "matrix_script"` branch
- `gateway/app/services/operator_visible_surfaces/publish_readiness.py::compute_publish_readiness` — single PR-1 producer; consumed read-only
- `gateway/app/services/operator_visible_surfaces/advisory_emitter.py::emit_advisories` — closed L4 advisory taxonomy; mirrored verbatim through `publish_readiness.blocking_advisories[]`
- `gateway/app/services/matrix_script/workbench_variation_surface.py::project_workbench_variation_surface` — variation_plan / copy_bundle / attribution_refs read-only
- `gateway/app/services/matrix_script/workbench_comprehension.py::derive_matrix_script_workbench_comprehension` — PR-U2 helper preserved verbatim
- `gateway/app/services/matrix_script/delivery_binding.py::project_delivery_binding` + `artifact_lookup` + `ARTIFACT_LOOKUP_UNRESOLVED` — read-only
- `gateway/app/services/matrix_script/delivery_comprehension.py::derive_matrix_script_delivery_comprehension` + `_artifact_status_label_zh` — operator-language artifact-status labels reused
- `gateway/app/services/matrix_script/closure_binding.py::get_closure_view_for_task` — read-only; never lazy-creates a closure on the workbench path
- `gateway/app/services/matrix_script/create_entry.py` — `task["config"]["entry"]` shape: `topic / source_script_ref / language_scope / target_platform / variation_target_count / tone_hint / audience_hint / length_hint / product_ref / operator_notes`
- `gateway/app/services/matrix_script/phase_b_authoring.py` — `LENGTH_PICKS` / `slot.length_hint` source for the 时长 quality item
- `gateway/app/routers/matrix_script_closure.py` — existing `POST /api/matrix-script/closures/{task_id}/events` route accepts the additive `review_zone` payload field automatically once the closure validator allows it (no router edit required)
- `gateway/app/services/task_router_presenters.py:445` — single callsite that wires the bundle into `task_json["operator_surfaces"]` (no edit; existing seam reused)
- `gateway/app/templates/task_workbench.html:270-609` — existing `panel_kind == "matrix_script"` template branch extended with four new panel blocks

### 2.6 Conflicts found
- **MS-W5 contract touch**: the OWC-MS gate spec §3 MS-W5 explicitly authorises the `review_zone` enum extension as the **only** contract touch in PR-2. The current `apply_event` for `operator_note` validated only `payload.operator_publish_notes` and recorded no zone. Resolution: PR-2 adds (a) `REVIEW_ZONE_VALUES = frozenset({"subtitle", "dub", "copy", "cta"})`; (b) optional validation in the `operator_note` branch — when `payload.review_zone` is present, it MUST be in `REVIEW_ZONE_VALUES`, else `ClosureValidationError`; (c) when valid, the `review_zone` value is recorded onto the appended `feedback_closure_records[]` entry as an additive optional key. Legacy `operator_note` events without `review_zone` remain valid. The closure shape envelope, the `variation_feedback[]` row shape, the closed `EVENT_KINDS` set, and `ACTOR_KINDS` are all unchanged. Contract addendum at `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` §"Operator review zone tag (additive, OWC-MS PR-2 — 2026-05-05)" pins the additive enum + the field's optionality.
- No other authority/code conflict found.

## 3. Files Changed

### New files
- `gateway/app/services/matrix_script/script_structure_view.py` — MS-W3 read-view helper (`derive_matrix_script_script_structure_view(task)`).
- `gateway/app/services/matrix_script/preview_compare_view.py` — MS-W4 view helper (`derive_matrix_script_preview_compare_view(variation_surface, delivery_binding, publish_readiness, line_specific_panel, *, closure=None)`).
- `gateway/app/services/matrix_script/review_zone_view.py` — MS-W5 view helper (`derive_matrix_script_review_zone_view(variation_surface, closure, line_specific_panel)`).
- `gateway/app/services/matrix_script/qc_diagnostics_view.py` — MS-W6 view helper (`derive_matrix_script_qc_diagnostics_view(publish_readiness, delivery_comprehension, variation_surface, line_specific_panel)`).
- `gateway/app/services/tests/test_matrix_script_script_structure_view.py` — 26 import-light test cases.
- `gateway/app/services/tests/test_matrix_script_preview_compare_view.py` — 22 import-light test cases.
- `gateway/app/services/tests/test_matrix_script_review_zone_view.py` — 16 import-light test cases.
- `gateway/app/services/tests/test_matrix_script_qc_diagnostics_view.py` — 28 import-light test cases (parametric × 10 closed-enum codes for `head_reason` translation included).
- `gateway/app/services/tests/test_matrix_script_workbench_review_zone_event.py` — 14 import-light test cases for the additive `review_zone` enum on `apply_event` (parametric × 4 closed enum values included).
- `gateway/app/services/tests/test_matrix_script_workbench_pr2_wiring.py` — 9 wiring + isolation cases.
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR2_WORKBENCH_FIVE_PANEL_EXECUTION_LOG_v1.md` — this file.

### Modified files
- `gateway/app/services/matrix_script/publish_feedback_closure.py` — additive `REVIEW_ZONE_VALUES` constant; optional validation in the `operator_note` branch of `apply_event`; recorded onto the appended `feedback_closure_records[]` entry as an optional key. The `variation_feedback[]` row shape, the closed `EVENT_KINDS` set, `ACTOR_KINDS`, and `CHANNEL_METRICS_KEYS` are all unchanged.
- `gateway/app/services/operator_visible_surfaces/wiring.py` — extended the existing `panel_kind == "matrix_script"` branch in `build_operator_surfaces_for_workbench` to attach four new bundle keys (`matrix_script_script_structure / matrix_script_preview_compare / matrix_script_review_zone / matrix_script_qc_diagnostics`); reads closure read-only via `get_closure_view_for_task(task_id)`. Hot Follow / Digital Anchor / Baseline workbench branches are byte-stable.
- `gateway/app/templates/task_workbench.html` — extended the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` block (no new branch). Added: (i) Workbench A panel BEFORE the existing Variation Panel (B); (ii) Workbench C / D / E panels AFTER the existing Variation Panel close; (iii) four new bundle setters at the top of the matrix_script branch (`ms_script_structure / ms_preview_compare / ms_review_zone / ms_qc_diagnostics`). The PR-U2 comprehension block, the Variation Panel block, the §8.E Hot Follow whitelist (`{% if task.kind == "hot_follow" %}` around four contiguous Hot Follow regions), and the §8.G Axes table item-access pattern (`axis["values"]`) are all preserved verbatim.
- `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` — appended §"Operator review zone tag (additive, OWC-MS PR-2 — 2026-05-05)" documenting the closed `review_zone` enum on the `operator_note` payload + the recorded position on `feedback_closure_records[]`. Strictly additive; no widening; no weakening; no removal.

### NOT modified
- Hot Follow source files (any path containing `hot_follow`).
- Digital Anchor source files (any path under `gateway/app/services/digital_anchor/`).
- Asset Supply files (`gateway/app/services/asset/*`).
- Any contract under `docs/contracts/` other than the closure contract addendum named above.
- Any sample under `schemas/`.
- Any worker / runtime / capability-adapter file.
- `gateway/app/templates/tasks.html` — out of scope for PR-2 (MS-W1/W2 land in OWC-MS PR-1, already merged).
- `gateway/app/templates/task_publish_hub.html` — out of scope for PR-2 (MS-W7/W8 land in OWC-MS PR-3).
- `gateway/app/services/task_router_presenters.py` — the existing seam at line 445 already calls `build_operator_surfaces_for_workbench` and attaches the bundle into `task_json["operator_surfaces"]`. No edit.
- `gateway/app/routers/matrix_script_closure.py` — existing route accepts the additive `review_zone` payload field automatically. No edit.
- `gateway/app/services/matrix_script/closure_binding.py` — read-only via `get_closure_view_for_task`. No edit.
- `gateway/app/services/matrix_script/workbench_variation_surface.py` — Phase B variation surface preserved verbatim.
- `gateway/app/services/matrix_script/workbench_comprehension.py` — PR-U2 helper preserved verbatim.
- `gateway/app/services/matrix_script/delivery_binding.py` — Phase C / B4 / PR-3 zoning preserved verbatim.
- `gateway/app/services/matrix_script/delivery_comprehension.py` — PR-U3 helper consumed read-only.
- `gateway/app/services/matrix_script/task_card_summary.py` — PR-U1 helper preserved.
- `gateway/app/services/matrix_script/task_area_convergence.py` — OWC-MS PR-1 helper preserved.

## 4. Why scope is minimal and isolated

- Four new service modules (one per panel — pure projection over already-existing surfaces).
- One new dedicated test module per service module + one closure-event additive-validation module + one wiring/isolation module.
- One existing seam modified: `build_operator_surfaces_for_workbench` (matrix_script branch only).
- One template seam modified: `task_workbench.html` matrix_script branch (Workbench A / C / D / E inserted around the existing Variation Panel; Hot Follow / Digital Anchor / baseline branches bytewise unchanged; PR-U2 comprehension block + §8.E Hot Follow whitelist + §8.G item-access pattern preserved verbatim).
- One contract addendum (the additive `review_zone` enum on `operator_note` payload — explicitly authorised by gate spec §3 MS-W5 as "the only contract touch").
- No packet truth, validator rule, schema, sample, or template-truth mutation outside the additive `review_zone` enum.
- No new endpoint; review actions write through the existing `POST /api/matrix-script/closures/{task_id}/events` route per Recovery PR-3.
- No second truth source for publishability / final_provenance / advisories.
- No durable persistence backend swap; the closure store remains in-process per Recovery red lines.
- No provider / model / vendor / engine identifier admitted into any payload (boundary tested recursively in the wiring-isolation test).

## 5. Tests Run

Local Python 3.9.6 (the unrelated `gateway/app/config.py` PEP 604 collection issue on `str | None` Field defaults remains a pre-existing repo baseline issue documented across PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 logs; affected files: `test_matrix_script_phase_b_authoring.py`, `test_matrix_script_source_script_ref_shape.py`, `test_matrix_script_workbench_dispatch.py`, `test_new_tasks_surface.py`. Confirmed pre-existing on `main`; not caused by this PR. CI on Python 3.10+ runs the full set.).

OWC-MS PR-2 dedicated test modules:
- `test_matrix_script_script_structure_view.py` — **26/26 PASS**.
- `test_matrix_script_preview_compare_view.py` — **22/22 PASS**.
- `test_matrix_script_review_zone_view.py` — **16/16 PASS**.
- `test_matrix_script_qc_diagnostics_view.py` — **28/28 PASS** (parametric × 10 head_reason codes included).
- `test_matrix_script_workbench_review_zone_event.py` — **14/14 PASS** (closure additive-validation + back-compat + cross-event-kind isolation).
- `test_matrix_script_workbench_pr2_wiring.py` — **9/9 PASS** (bundle attachment + Hot Follow / Digital Anchor / Baseline isolation + cross-surface head_reason consistency + closure shape unchanged).

**Subtotal: 115 PASS / 0 FAIL** for new PR-2 tests. Gate spec §5.2 ≥40 test floor: PASS (115 cases).

Adjacent regression (no behavior change expected; verifies byte-isolation):
- `test_matrix_script_closure_binding.py` — PASS
- `test_matrix_script_closure_publish_hub_wiring.py` — PASS
- `test_matrix_script_closure_surface_boundary.py` — PASS
- `test_matrix_script_b4_artifact_lookup.py` — PASS
- `test_matrix_script_delivery_zoning.py` — PASS
- `test_matrix_script_delivery_comprehension.py` — PASS
- `test_matrix_script_workbench_comprehension.py` — PASS
- `test_matrix_script_task_card_summary.py` — PASS
- `test_matrix_script_task_area_convergence.py` — PASS (OWC-MS PR-1 substrate)
- `test_matrix_script_f2_minting_flow.py` — PASS
- `test_publish_readiness_unified_producer.py` — PASS
- `test_publish_readiness_surface_alignment.py` — PASS
- `test_final_provenance_emission.py` — PASS
- `test_digital_anchor_create_entry.py` — PASS
- `test_digital_anchor_closure_binding.py` — PASS
- `test_digital_anchor_workspace_wiring.py` — PASS
- `test_digital_anchor_surface_boundary.py` — PASS
- `test_asset_library_read_only.py` — PASS
- `test_asset_promote_lifecycle.py` — PASS
- `test_asset_surface_boundary.py` — PASS

**Adjacent: 372 PASS / 0 FAIL.**

**Aggregate: 487 PASS / 0 FAIL** on Python 3.9 import-light set (115 new + 372 adjacent).

## 6. Acceptance Mapping (against `owc_ms_gate_spec_v1.md` §3 + §6)

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| MS-W3 — Workbench A 脚本结构区 read-view (Hook / Body / CTA / 关键词 / 禁用词) visible on `task_workbench.html` matrix_script branch | PASS | `derive_matrix_script_script_structure_view` + new `data-role="matrix-script-script-structure-panel"` block; tests `test_sections_render_three_in_order`, `test_section_bodies_render_unauthored_sentinel`, `test_taxonomy_renders_two_in_order`, `test_taxonomy_renders_unauthored_sentinel` |
| MS-W3 — no operator authoring of `source_script` (read-only invariant) | PASS | `test_phase_b_authoring_notice_cites_owc_ms_gate_spec_section_4_1`; helper carries `phase_b_authoring_forbidden_label_zh`; `source_script_ref` rendered verbatim with `STATUS_OPAQUE_REF` and never dereferenced |
| MS-W4 — Workbench C 预览对比区 (multi-variation preview / 差异项提示 / 推荐版本标识) visible on `task_workbench.html` matrix_script branch | PASS | `derive_matrix_script_preview_compare_view` + new `data-role="matrix-script-preview-compare-panel"` block; tests `test_variation_rows_one_per_cell_with_axis_selections`, `test_diff_hints_list_one_per_axis_with_distinct_values`, `test_diff_hints_invariant_axis_marked_non_differing`, `test_recommended_publishable_candidate_when_publishable_and_unpublished`, `test_recommended_blocked_when_publish_readiness_blocked` |
| MS-W4 — `artifact_lookup` consumed from existing Phase C delivery binding (no second truth) | PASS | `test_preview_status_unresolved_from_sentinel`, `test_preview_status_current_fresh_from_handle`, `test_preview_status_historical_from_handle` — all read from `_artifact_status_label_zh` on the variation_manifest row |
| MS-W4 — recommended-version derives from PR-1 unified `publish_readiness` ONLY (no second producer) | PASS | `test_recommended_publishable_candidate_when_publishable_and_unpublished`, `test_recommended_blocked_when_publish_readiness_blocked`, `test_recommended_undetermined_when_already_published`, `test_recommended_undetermined_when_no_publish_readiness_provided` |
| MS-W5 — Workbench D 校对区 (字幕 / 配音 / 文案 / CTA) visible on `task_workbench.html` matrix_script branch | PASS | `derive_matrix_script_review_zone_view` + new `data-role="matrix-script-review-zone-panel"` block; test `test_zones_emit_four_in_stable_order` asserts exactly the four labels (字幕校对 / 配音校对 / 文案校对 / CTA 校对) |
| MS-W5 — review actions write through the existing closure event endpoint (no new endpoint) | PASS | `test_zone_payload_shape_example_uses_existing_endpoint_and_event_kind`, `test_closure_endpoint_explanation_names_recovery_pr3_endpoint` — endpoint template is exactly `POST /api/matrix-script/closures/{task_id}/events` from Recovery PR-3 |
| MS-W5 — additive `review_zone` enum is the only contract touch (closed enum subtitle / dub / copy / cta) | PASS | `test_review_zone_values_is_exactly_four_zones`, `test_review_zone_values_does_not_widen_event_kinds_or_actor_kinds`, `test_review_zone_values_does_not_widen_channel_metrics_keys`, `test_operator_note_with_review_zone_does_not_widen_variation_feedback_row`, `test_closure_envelope_keys_unchanged_under_review_zone_writes`; contract addendum at `publish_feedback_closure_contract_v1.md` §"Operator review zone tag (additive, OWC-MS PR-2 — 2026-05-05)" |
| MS-W5 — legacy `operator_note` events without `review_zone` remain valid | PASS | `test_legacy_operator_note_without_review_zone_accepted` |
| MS-W5 — unknown `review_zone` values raise and do not append | PASS | `test_operator_note_with_unknown_review_zone_raises_and_does_not_append` |
| MS-W6 — Workbench E 质检与诊断区 (风险 / 合规 / 时长 / 清晰度 / 字幕可读性 / 产物状态 / ready gate 解释) visible on `task_workbench.html` matrix_script branch | PASS | `derive_matrix_script_qc_diagnostics_view` + new `data-role="matrix-script-qc-diagnostics-panel"` block; tests `test_quality_items_always_three_rows`, `test_compliance_items_enumerate_no_provider_and_no_phase_b_reminders`, `test_artifact_status_items_flatten_lanes_into_rows` |
| MS-W6 — PR-1 L4 advisory_emitter output rendered verbatim (no new advisory rule) | PASS | `test_risk_items_mirror_publish_readiness_blocking_advisories` asserts the helper passes through `id / level / kind / operator_hint / explanation / recommended_next_action` from `publish_readiness.blocking_advisories[]` without minting new ids |
| MS-W6 — `head_reason` consumed from PR-1 unified producer (closed enum) | PASS | `test_head_reason_known_codes_translate` (parametric over the 10 closed codes), `test_head_reason_unknown_falls_through_verbatim`, `test_qc_diagnostics_head_reason_equals_publish_readiness_head_reason` (cross-surface consistency) |
| Hot Follow byte-isolation | PASS | No file under `gateway/app/services/hot_follow*` or template `hot_follow_*.html` modified; `task_workbench.html` `{% if task.kind == "hot_follow" %}` whitelist around four contiguous Hot Follow regions preserved verbatim; `test_hot_follow_task_bundle_carries_no_pr2_panel_keys` asserts behavioral isolation |
| Digital Anchor byte-isolation | PASS | No file under `gateway/app/services/digital_anchor/*` modified; `test_digital_anchor_task_bundle_carries_no_pr2_panel_keys` asserts behavioral isolation |
| Asset Supply consumed read-only | n/a | No Asset Supply file touched (PR-2 does not consume Asset Supply) |
| No PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 truth modified | PASS | Forbidden-scope audit §7 below |
| Product-Flow Module Presence rule (ENGINEERING_RULES §13) — modules visible on `task_workbench.html` | PASS | Reviewer can read `gateway/app/templates/task_workbench.html` matrix_script branch and confirm: Workbench A (`data-role="matrix-script-script-structure-panel"`), Variation Panel (existing — Workbench B; preserved), Workbench C (`data-role="matrix-script-preview-compare-panel"`), Workbench D (`data-role="matrix-script-review-zone-panel"`), Workbench E (`data-role="matrix-script-qc-diagnostics-panel"`) |
| Test floor ≥40 cases per gate spec §5.2 | PASS | 115 test cases shipped across six dedicated PR-2 test modules |

## 7. Forbidden-Scope Audit (against `owc_ms_gate_spec_v1.md` §4)

### §4.1 Truth-source / contract preservation
| Red line | Status |
| --- | --- |
| No Matrix Script packet truth mutation | clean — no packet schema or sample modified |
| No reopen of §8.A–§8.H correction chain | clean — no §8 artifact touched |
| No widening of `target_language`, canonical axes, or `source_script_ref` accepted-scheme set | clean — no scheme set or axis set modified |
| No operator-driven Phase B authoring (variation cells stay deterministically derived) | clean — `script_structure_view` exposes opaque `source_script_ref` + sentinel sections; `review_zone_view` writes only `operator_note` events; `phase_b_authoring_forbidden` notice cites OWC-MS gate spec §4.1 in two helpers |
| No `source_script_ref` repurposing | clean — helper renders the bare ref string for display only; no dereference |
| No new authoritative truth source for publishability | clean — `recommended_marker` consumes `publish_readiness.publishable + head_reason` only; PR-1 unified producer remains the only `publishable` truth source |
| No second producer for `final_provenance` (L3) or L4 advisory | clean — `risk_items` mirror `publish_readiness.blocking_advisories[]` verbatim; no advisory id minted |

### §4.2 Cross-line preservation
| Red line | Status |
| --- | --- |
| No Hot Follow file touched | clean |
| No Digital Anchor file touched | clean |
| No cross-cutting wiring change outside the existing `panel_kind == "matrix_script"` / `_ms_kind == "matrix_script"` branches | clean — `wiring.py` edit confined to the existing `panel_kind == "matrix_script"` branch in `build_operator_surfaces_for_workbench`; `task_workbench.html` edit confined to the existing `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` block |

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
| No provider / model / vendor / engine controls or operator selector | clean — boundary tested recursively via `test_bundle_carries_no_vendor_model_provider_engine_keys_recursively` (wiring) + per-helper validator R3 walks |
| No donor namespace import | clean — no `from swiftcraft.*` |
| No Asset Supply page / promote service / DAM expansion | clean |
| No React / Vite full rebuild or new component framework | clean — Jinja2 + minimal `data-role` attributes only |
| No durable persistence backend swap | clean — closure store remains in-process; helpers consume read-only via `get_closure_view_for_task` |
| No bundling of MS-W* slices | clean — only MS-W3..W6 land here; MS-W7/W8 deferred to OWC-MS PR-3 |

### §4.5 Closeout-paperwork independence
| Red line | Status |
| --- | --- |
| No forced advancement of prior closeout signoffs (recovery PR-1..PR-4 closeouts, Plan E phase closeouts, OWC-MS PR-1 closeout) | clean — none touched |

## 8. Residual Risks

- **In-process closure store**: when the gateway process restarts, `feedback_closure_records[]` resets to empty, so the per-variation per-zone history shown by Workbench D resets too. Acceptable per Recovery Decision §4.3 (minimum operator capability, not durable persistence). A later wave may swap the in-process store for a durable backend without changing the closure shape or any of the four PR-2 helpers.
- **Per-variation artifact provenance gap**: today's `matrix_script_delivery_binding_v1` carries one shared `artifact_lookup` on the `variation_manifest` row; the comprehension layer therefore applies the manifest-level status to every variation row in the preview-compare table. The `per_cell_artifact_granularity_note_zh` field on the helper output names the gap in operator language. A future variation-level provenance lands per-cell `artifact_lookup` without any change to `preview_compare_view.py`.
- **Outline Contract gap**: today's `task["config"]["entry"]` does not carry `hook / body / cta / keywords / forbidden_terms` payloads (the Outline Contract per matrix_script_product_flow §9.2 has not landed). The MS-W3 read-view exposes the structural skeleton with operator-language sentinels and explicitly cites the future Outline Contract. When the contract lands, only the helper's section/taxonomy projection switches from the sentinel to the real value — no template change required.
- **Recommended-version marker is coarse**: today's marker only buckets variations into `publishable_candidate / blocked_pending_publish_readiness / undetermined_pending_review` because per-variation `ready_gate` truth does not yet exist (the unified producer derives a single task-level `publishable`). Per-variation `recommended_marker` refinement requires per-variation L2/L4 truth, which is out of scope for OWC-MS PR-2.
- **Quality items 清晰度 + 字幕可读性 are unobservable**: the MS-W6 helper renders the `unobservable_pending_upstream` sentinel for these two items because the upstream provenance + subtitle review zone produce no observable signal yet. Operator-language explanation names the gating; future provenance upgrades populate the items without any template change.
- **Closure router payload guard accepts `review_zone`**: the existing router-side `_scrub_forbidden_keys` rejects keys containing `vendor / model_id / provider / engine` — `review_zone` does not match any of those fragments, so the additive enum reaches the closure validator unaffected. Verified by direct reading of `gateway/app/routers/matrix_script_closure.py:42-69`; not exercised by HTTP test in this PR (the HTTP cases auto-skip without FastAPI TestClient on Python 3.9). CI on Python 3.10+ exercises the HTTP path through the existing `test_matrix_script_closure_api.py` adjacent suite (no PR-2-specific HTTP test added because the route shape is unchanged).
- **Branch shape**: this PR uses the same branch as OWC-MS PR-1 (`claude/owc-ms-pr1-task-area-convergence`) per `git status` at session start; the working tree was clean and this is the next layer of OWC-MS work on that branch. The PR title and the `gh pr create` step disambiguate this as OWC-MS PR-2 (Workbench Five-Panel Convergence).

## 9. Exact Statement of What Remains for the Next PR

OWC-MS PR-3 — Matrix Script Delivery Convergence + 回填 Multi-Channel (MS-W7 + MS-W8) per `owc_ms_gate_spec_v1.md` §5. PR-3 may not start until this PR-2 is merged and reviewed. Claude stops after this PR-2 is opened.

## 10. References

- Gate spec: `docs/reviews/owc_ms_gate_spec_v1.md`
- Sister-phase gate spec: `docs/reviews/owc_da_gate_spec_v1.md`
- Predecessor docs PR: `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`
- Predecessor implementation PR: `docs/execution/APOLLOVEO_2_0_OWC_MS_PR1_TASK_AREA_EXECUTION_LOG_v1.md`
- Engineering rule binding: `ENGINEERING_RULES.md` §13 Product-Flow Module Presence
- Line-specific authority: `docs/product/matrix_script_product_flow_v1.md`
- Recovery PR-1 (publish_readiness producer): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`
- Recovery PR-3 (Matrix Script closure binding): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md`
- Closure contract addendum: `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` §"Operator review zone tag (additive, OWC-MS PR-2 — 2026-05-05)"
