# ApolloVeo 2.0 · OWC-MS PR-3 — Matrix Script Delivery Convergence + 回填 Multi-Channel — Execution Log v1

Date: 2026-05-05
Status: **MERGED to `main` on 2026-05-05T03:22:39Z as PR #125, squash commit `3d9954c`.** Final state after the §8.1 reviewer-fail correction pass (single-source MS-W7 + storage-independent wiring tests via the `publish_hub_pr3_attach` seam) and the Codex P1 fix for the no-closure backfill bundle shape.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC), Phase OWC-MS.
Phase Gate: [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md).
Predecessors: OWC authority/gate normalization PR (#121, squash commit `27aa950`); OWC-MS PR-1 (Task Area Workflow Convergence — PR #122, squash commit `0b23605`); OWC-MS PR-2 (Workbench Five-Panel Convergence — PR #123, squash commit `c7a5a89`); post-merge housekeeping PR #124 (`d2ad7a8`); Operator Capability Recovery PR-1..PR-4 (all merged 2026-05-04).

## 1. Scope

OWC-MS PR-3 is the third of three implementation PRs in the Operator Workflow Convergence Wave for Matrix Script. It lands the OWC-MS gate spec §3 Delivery Center scope **for the two slices in the binding-and-exhaustive set**:

- **MS-W7 — Delivery Center copy_bundle exposure**. Operator-language Delivery Center row exposing 标题 / hashtags / CTA / 评论关键词 (`docs/product/matrix_script_product_flow_v1.md` §7.1 标准交付物). Each subfield reads from existing closed truth — `_build_copy_bundle(task)` (the existing publish-hub `copy_bundle` projection that ships caption / hashtags / comment_cta) and `task["config"]["entry"]` (closed Phase A entry payload: topic / target_platform / audience_hint / tone_hint). When the specific source is empty, the subfield falls back to `STATUS_UNRESOLVED` with operator-language explanation citing the gating future contract (Outline Contract per product-flow §9.2 for 标题; future copy 投射 contract for hashtags / 评论关键词). The fallback is per-subfield, never panel-wide (§8.1.1 PR-2 reviewer-fail correction precedent — per-field unresolved fallback, never panel-wide replacement). Validator R3 forbidden tokens (vendor / model_id / provider / engine) are scrubbed defensively per-subfield.
- **MS-W8 — Delivery 回填 multi-channel rendering**. Operator-language multi-channel 回填 view per `docs/product/matrix_script_product_flow_v1.md` §7.3, rendering one lane per `closure.variation_feedback[]` row. Each lane carries six fields in stable order: 发布渠道 / 账号 ID / 发布时间 / 发布链接 / 发布状态 / 指标入口（snapshot）. All reads pass through the contract-frozen `matrix_script_publish_feedback_closure_v1` surface (`closure.variation_feedback[]` + `closure.feedback_closure_records[]` + `channel_metrics[]`) — single truth path; no second producer. **`account_id` is rendered as an explicit tracked-gap row** (`status_code: "unsourced_pending_capture_capability"`) because the closure contract carries no `account_id` field today and gate spec §3 MS-W8 forbids closure schema widening. Validator R3 forbidden tokens are scrubbed defensively per-field.

Out of scope (carried by OWC-MS Closeout + OWC-DA + later phases):

- OWC-MS Closeout aggregating audit + signoff — paperwork-only PR opening **after** OWC-MS PR-3 merges; not started in this PR per the user's mission ("Stop after opening OWC-MS PR-3. Do not start OWC-MS Closeout.").
- Per-account fanout: today's closure binds `task_id → closure_id` 1:1 and a single `variation_feedback[]` row covers all accounts publishing the same variation (last-write-wins). A future per-account dimension would land additional rows; until then, the per-row single-account rendering is the correct projection and the 账号 ID gap is surfaced explicitly.
- Publish account capture capability — gated to a future OWC scope authoring step.
- Digital Anchor surface convergence — OWC-DA.
- Hot Follow modifications — out of all OWC scope (Hot Follow baseline byte-isolated).
- Plan A live-trial reopen — gated on OWC-MS Closeout + OWC-DA Closeout + separate trial re-entry review.

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md` (no private memory; native state ownership)
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md` (with §13 Product-Flow Module Presence)
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 OWC wave authority
- `docs/reviews/owc_ms_gate_spec_v1.md` §3 (MS-W7 + MS-W8 binding scope), §4 (forbidden scope), §5.1 (per-PR file isolation), §5.2 (≥30 test floor for PR-3), §6 (MS-A1..MS-A8 evidence), §7 (preserved freezes), §8 (stop conditions), §9 (R1..R5 review)
- `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR1_TASK_AREA_EXECUTION_LOG_v1.md`
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR2_WORKBENCH_FIVE_PANEL_EXECUTION_LOG_v1.md`

### 2.3 Line-specific execution authority (binding)
- `docs/product/matrix_script_product_flow_v1.md` §7.1 (标准交付物 — copy_bundle 标题 / hashtags / CTA / 评论关键词); §7.2 (发布规则 — 历史成功 vs 当前尝试 must remain separated; publish 只消费 authoritative projection); §7.3 (回填对象 — 发布渠道 / 账号 ID / 发布时间 / 发布链接 / 发布状态 / 指标入口)

### 2.4 Factory-wide / surface authority (read-only)
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md` §5.4 Delivery Center (Matrix Script row)

### 2.5 Existing code surfaces consumed (not mutated)
- `gateway/app/services/task_view_helpers.py::publish_hub_payload` — single seam where the matrix_script publish-hub branch lives; extended only inside the existing `kind_value == "matrix_script"` branch
- `gateway/app/services/task_view_helpers.py::_build_copy_bundle(task)` — pre-existing publish-hub `copy_bundle` projection (caption / hashtags / comment_cta / link_text / publish_time_suggestion); read-only
- `gateway/app/services/matrix_script/closure_binding.py::get_closure_view_for_task` — read-only; never lazy-creates a closure on the publish-hub read path
- `gateway/app/services/matrix_script/publish_feedback_closure.py` — `variation_feedback[]` row shape + `feedback_closure_records[]` + `channel_metrics[]` + closed enums `EVENT_KINDS / ACTOR_KINDS / PUBLISH_STATUS_VALUES / CHANNEL_METRICS_KEYS / REVIEW_ZONE_VALUES`. **Read-only** — no enum widening.
- `gateway/app/services/matrix_script/create_entry.py` — `task["config"]["entry"]` shape: `topic / target_platform / audience_hint / tone_hint / length_hint / product_ref / operator_notes`. Read-only.
- `gateway/app/services/matrix_script/delivery_binding.py` — Phase C / B4 / Plan E zoning preserved (read-only consumer)
- `gateway/app/services/matrix_script/delivery_comprehension.py` — PR-U3 helper (read-only consumer; PR-3 sits beside it, not on top of it)
- `gateway/app/templates/task_publish_hub.html` — existing `_ms_kind == "matrix_script"` gate at lines 266–381; extended with two new server-rendered cards inside the same gate

### 2.6 Conflicts found
- **MS-W7 wording vs repo surface (resolved)**: The OWC-MS gate spec §3 MS-W7 references "existing `variation_manifest.copy` projection" but the actual repo surface is the existing publish-hub `_build_copy_bundle(task)` (caption / hashtags / comment_cta / link_text / publish_time_suggestion) plus the `task["config"]["entry"]` payload. The gate spec §3 MS-W7 also explicitly authorizes a tracked-gap fallback ("If the field is not projection-ready, mark as a tracked gap; do NOT add packet truth in this wave."). Resolution: helper consumes both surfaces with per-subfield precedence (caption → topic for 标题; hashtags-only for hashtags; target_platform for CTA; comment_cta → audience+tone for 评论关键词); per-subfield `STATUS_UNRESOLVED` only when its specific source is empty. **No contract change.**
- **MS-W8 account_id absence (resolved)**: `matrix_script_publish_feedback_closure_v1` has no `account_id` on `variation_feedback[]` rows or `channel_metrics[]` snapshots. Gate spec §3 MS-W8 forbids closure schema widening. The user mission's MS-W8 rule forbids widening except inside approved OWC scope, and `account_id` is NOT in approved OWC scope. Resolution: render `account_id` with the closed `status_code = "unsourced_pending_capture_capability"` operator-language tracked-gap label naming "publish 账号采集能力尚未上线". **No contract change.**
- No other authority/code conflict found.

## 3. Files Changed

### New files (3 + 3 tests + 1 execution log)
- `gateway/app/services/matrix_script/delivery_copy_bundle_view.py` — MS-W7 helper `derive_matrix_script_delivery_copy_bundle(task, *, base_copy_bundle=None)`. Closed shape: `{is_matrix_script, panel_title_zh, panel_subtitle_zh, subfields[], unresolved_count, tracked_gap_summary_zh}` with one closed-shape subfield per `{title, hashtags, cta, comment_keywords}`.
- `gateway/app/services/matrix_script/delivery_backfill_view.py` — MS-W8 helper `derive_matrix_script_delivery_backfill(closure)`. Closed shape: `{is_matrix_script, panel_title_zh, panel_subtitle_zh, field_legend_zh, lanes[], lane_count, tracked_gap_summary_zh}` with one lane per `variation_feedback[]` row carrying six closed-shape fields per lane.
- `gateway/app/services/tests/test_matrix_script_delivery_copy_bundle_view.py` — **38 dedicated MS-W7 cases** (cross-line isolation, four-subfield order, per-subfield precedence, per-subfield unresolved fallback independence, forbidden-token scrub, validator R3 recursive walk, no input mutation, closed-shape invariants).
- `gateway/app/services/tests/test_matrix_script_delivery_backfill_view.py` — **40 dedicated MS-W8 cases** (cross-line isolation by surface + line_id, lane count + order, six-field closed order, channel resolution from channel_metrics, account always tracked-gap, publish_time precedence operator_publish/platform_callback over channel_metrics fallback, publish_url + publish_status closed enum, out-of-enum graceful degrade, metrics_snapshot key-set discipline, closed-set sanity check vs closure contract, validator R3 recursive walk, no input mutation, no closure schema widening invariant).
- `gateway/app/services/tests/test_matrix_script_publish_hub_pr3_wiring.py` — **15 wiring + isolation cases** (matrix_script payload carries both PR-3 keys; Hot Follow / Digital Anchor / Baseline payloads carry NEITHER; backfill helper reads same closure as existing PR-3 block; PR-2 / PR-U3 keys preserved; seam never lazy-creates closure on read path; closed forbidden-token recursive walk; no `task["config"]["entry"]` mutation). Auto-skips on Python 3.9 per the documented `gateway/app/config.py:43` PEP-604 baseline limitation; CI on 3.10+ runs the full set.
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PR3_DELIVERY_BACKFILL_EXECUTION_LOG_v1.md` — this file.

### Modified files (2)
- `gateway/app/services/task_view_helpers.py` — extended the existing `kind_value == "matrix_script"` branch in `publish_hub_payload(task)` to attach `payload["matrix_script_delivery_copy_bundle"]` (consuming `payload["copy_bundle"]` as the existing publish-hub projection input + `task` as the entry-payload source) and `payload["matrix_script_delivery_backfill"]` (consuming `payload["matrix_script_publish_feedback_closure"]` as the closure input — same closure view the existing Recovery PR-3 block reads). Hot Follow / Digital Anchor / Baseline branches are byte-stable. Defense-in-depth `try/except` mirrors the PR-U3 / Recovery PR-3 patterns: a projection error never breaks the publish hub; the keys default to `{}` instead.
- `gateway/app/templates/task_publish_hub.html` — extended the existing `{% if _ms_kind == "matrix_script" %}` block (line 266–381) with **two new server-rendered cards**: `matrix-script-delivery-copy-bundle-block` (renders the four MS-W7 subfields with per-subfield label / value / status / unresolved-explanation) and `matrix-script-delivery-backfill-block` (renders one lane per variation_id with the six MS-W8 fields + tracked-gap footnote). Two matching JS renderer functions (`renderMatrixScriptDeliveryCopyBundle` / `renderMatrixScriptDeliveryBackfill`) inserted alongside the existing `renderMatrixScriptDeliveryComprehension` function. Two new call-sites in `fetchPublishHub` next to the existing PR-U3 / Recovery PR-3 renderers. Hot Follow / Digital Anchor / Baseline blocks bytewise unchanged. PR-U3 comprehension block + Recovery PR-3 closure block + Digital Anchor closure block all preserved verbatim.

### NOT modified
- Any contract under `docs/contracts/`. The publish-feedback closure contract was already extended for MS-W5 in PR-2; PR-3 makes **zero further contract touches** (gate spec §3 MS-W7/W8 explicitly say "If the field is not projection-ready, mark as a tracked gap; do NOT add packet truth in this wave" / "Entirely projection-side; no closure schema widening").
- Any packet schema / sample / test fixture.
- `gateway/app/services/matrix_script/publish_feedback_closure.py` (closure shape + `EVENT_KINDS / ACTOR_KINDS / PUBLISH_STATUS_VALUES / CHANNEL_METRICS_KEYS / REVIEW_ZONE_VALUES` byte-stable).
- `gateway/app/services/matrix_script/closure_binding.py` (read-only consumer remains read-only; PR-3 reads via the same `get_closure_view_for_task` Recovery PR-3 introduced).
- `gateway/app/services/matrix_script/delivery_binding.py` (Phase C / B4 / Plan E zoning preserved verbatim).
- `gateway/app/services/matrix_script/delivery_comprehension.py` (PR-U3 helper preserved verbatim).
- `gateway/app/services/matrix_script/script_structure_view.py` / `preview_compare_view.py` / `review_zone_view.py` / `qc_diagnostics_view.py` (PR-2 helpers preserved verbatim).
- `gateway/app/services/matrix_script/workbench_variation_surface.py` / `workbench_comprehension.py` / `task_card_summary.py` / `task_area_convergence.py` / `create_entry.py` / `phase_b_authoring.py` / `source_script_ref_minting.py` (preserved verbatim).
- `gateway/app/services/operator_visible_surfaces/wiring.py` (PR-3 wires through `publish_hub_payload` directly per the existing seam — `wiring.py` is for the workbench bundle).
- `gateway/app/services/operator_visible_surfaces/publish_readiness.py` / `advisory_emitter.py` (single PR-1 producers; consumed read-only by Recovery PR-3 and PR-2 — neither extended in PR-3).
- `gateway/app/routers/matrix_script_closure.py` (no new endpoint; PR-3 has no write path).
- Hot Follow source files (any path containing `hot_follow`).
- Digital Anchor source files (any path under `gateway/app/services/digital_anchor/`).
- Asset Supply files (`gateway/app/services/asset/*`).
- `gateway/app/templates/tasks.html` (MS-W1/W2 surface — out of scope for PR-3; OWC-MS PR-1 substrate).
- `gateway/app/templates/task_workbench.html` (MS-W3..W6 surface — out of scope for PR-3; OWC-MS PR-2 substrate).
- Any worker / runtime / capability-adapter file.

## 4. Why scope is minimal and isolated

- **Two new service modules** (one per slice — pure projection over already-existing surfaces). Both helpers live under `gateway/app/services/matrix_script/` per the §5.1 file-isolation contract.
- **One new dedicated test module per service module** + **one wiring/isolation module**. Total dedicated PR-3 test modules: three. Total active PR-3 tests on Python 3.9: 78 passing (38 + 40); 15 wiring tests auto-skip on 3.9 and run on CI 3.10+.
- **One existing seam modified**: `publish_hub_payload` matrix_script branch only. Hot Follow branch (Hot Follow has its own dedicated builder, not this entry) and Digital Anchor branch (separate `kind_value == "digital_anchor"` block) bytewise unchanged.
- **One template seam modified**: `task_publish_hub.html` `_ms_kind == "matrix_script"` block only. PR-U3 comprehension block + Recovery PR-3 closure block + Digital Anchor closure block all preserved verbatim. Hot Follow / Baseline render paths unchanged.
- **Zero contract addenda**. The OWC-MS gate spec §3 MS-W7/W8 explicitly bind "no packet truth" / "no closure schema widening" — PR-3 honors that verbatim.
- **No new endpoint**. The 回填 lanes are read-only projections; events still write through the existing Recovery PR-3 route `POST /api/matrix-script/closures/{task_id}/events` (no router edit).
- **No second truth source for publishability / final_provenance / advisories.** PR-1 unified `publish_readiness` producer remains the only `publishable` truth source (consumed by PR-2 MS-W4/W6 and PR-U3); PR-3 does not call it directly because the 回填 view is purely a closure-side projection.
- **No durable persistence backend swap**. Closure store remains in-process per Recovery red lines.
- **No provider / model / vendor / engine identifier admitted into any payload** (boundary tested recursively in both helper test modules + the wiring test).

## 5. Tests Run

Local Python 3.9.6 (the unrelated `gateway/app/config.py:43` PEP 604 collection issue on `str | None` Field defaults remains a pre-existing repo baseline issue documented across PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 / OWC-MS PR-2 logs; affected files include `test_matrix_script_phase_b_authoring.py`, `test_matrix_script_source_script_ref_shape.py`, `test_matrix_script_workbench_dispatch.py`, `test_new_tasks_surface.py`, and the new `test_matrix_script_publish_hub_pr3_wiring.py`. CI on Python 3.10+ runs the full set).

OWC-MS PR-3 dedicated test modules:

- `test_matrix_script_delivery_copy_bundle_view.py` — **38/38 PASS** (cross-line isolation × 4 kinds; subfields-emit-four-in-stable-order; per-subfield precedence × 4 subfields × 2-3 sources each; per-subfield unresolved fallback independence; tracked-gap summary emission; forbidden token scrub × 4 fragments × 3 source types; validator R3 recursive walk; no input mutation; closed-shape invariants).
- `test_matrix_script_delivery_backfill_view.py` — **40/40 PASS** (cross-line isolation by surface + line_id; lane count + label; six-field closed order; field-legend stable order; channel resolution / unresolved; account-tracked-gap-always; publish_time precedence operator_publish / platform_callback / channel_metrics_captured_at / unresolved; latest-publish-event-wins; publish_url resolved / unresolved; publish_status × 4 closed enum values + out-of-enum graceful degrade + closed-enum mirror sanity check vs `PUBLISH_STATUS_VALUES`; metrics_snapshot latest-snapshot + omit-keys-outside-closed-set + operator-language metric labels; forbidden-token scrub recursive × 4 fragments + channel_id scrub + publish_url scrub; closed-shape per-field invariants; lane carries publish_event_count + channel_metrics_count; helper does not mutate closure; helper never widens `EVENT_KINDS / ACTOR_KINDS / CHANNEL_METRICS_KEYS`).
- `test_matrix_script_publish_hub_pr3_wiring.py` — **15/15 SKIPPED on 3.9 (clean)** + **15/15 PASS on CI Python 3.10+** (matrix_script payload carries both PR-3 keys; Hot Follow / Digital Anchor / Baseline payloads carry NEITHER; closure-aware backfill rendering; copy-bundle title falls back through publish-hub caption → entry topic; backfill helper reads same closure as existing PR-3 block; PR-2 / PR-U3 keys preserved; seam never lazy-creates closure on read path; closed forbidden-token recursive walk × 4 fragments; PR-3 + PR-U3 + Recovery PR-3 attach side-by-side; helper does not mutate `task["config"]["entry"]`).

**Subtotal: 78 PASS / 15 SKIPPED / 0 FAIL** for new PR-3 tests on Python 3.9 (38 + 40 active; 15 wiring auto-skip per documented baseline). Gate spec §5.2 ≥30 test floor: **PASS** (78 active cases, 2.6× the floor).

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
- `test_matrix_script_script_structure_view.py` — PASS (OWC-MS PR-2 substrate)
- `test_matrix_script_preview_compare_view.py` — PASS (OWC-MS PR-2 substrate)
- `test_matrix_script_review_zone_view.py` — PASS (OWC-MS PR-2 substrate)
- `test_matrix_script_qc_diagnostics_view.py` — PASS (OWC-MS PR-2 substrate)
- `test_matrix_script_workbench_pr2_wiring.py` — PASS (OWC-MS PR-2 substrate)
- `test_matrix_script_review_zone_submit_http.py` — PASS (HTTP-side cases auto-skip on Python 3.9 per PEP-604 baseline)
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

**Adjacent: 562 PASS / 22 SKIPPED / 0 FAIL** (415 matrix_script suite + 147 cross-cutting Recovery / Digital Anchor / Asset Supply suite).

**Aggregate: 640 PASS / 37 SKIPPED / 0 FAIL** on Python 3.9 import-light set (78 new + 562 adjacent; 15 PR-3 wiring + 22 prior-PR HTTP cases auto-skip).

## 6. Acceptance Mapping (against `owc_ms_gate_spec_v1.md` §3 + §6)

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| MS-W7 — Delivery Center copy_bundle row exposing 标题 / hashtags / CTA / 评论关键词 visible on `task_publish_hub.html` matrix_script branch | PASS | `derive_matrix_script_delivery_copy_bundle` + new `data-role="matrix-script-delivery-copy-bundle"` block; tests `test_subfields_emit_four_in_stable_order`, `test_subfield_label_zh_matches_product_flow_section_7_1` |
| MS-W7 — backed by existing projection (no new packet truth) | PASS | Helper signature consumes `task["config"]["entry"]` (closed Phase A entry contract) + `payload["copy_bundle"]` (existing publish-hub projection) only; tests `test_title_resolves_from_caption_when_present`, `test_title_falls_back_to_topic_when_caption_empty`, `test_hashtags_resolves_from_base_copy_bundle`, `test_cta_resolves_from_entry_target_platform`, `test_comment_keywords_resolves_from_comment_cta_first` |
| MS-W7 — tracked-gap fallback is per-subfield (never panel-wide) | PASS | `test_per_subfield_unresolved_fallback_does_not_replace_resolved_subfields` + per-subfield-unresolved tests + `test_unresolved_count_zero_when_all_subfields_resolved` |
| MS-W7 — does not add packet truth in this wave | PASS | No contract / schema / sample / packet file modified — see §3 NOT modified. `STATUS_UNRESOLVED` rows carry operator-language explanation pointing at the future Outline Contract / copy 投射 contract for compliance with gate spec §3 MS-W7. |
| MS-W8 — Delivery 回填 multi-channel lanes visible on `task_publish_hub.html` matrix_script branch | PASS | `derive_matrix_script_delivery_backfill` + new `data-role="matrix-script-delivery-backfill"` block; tests `test_lane_count_matches_variation_feedback_rows`, `test_lane_label_zh_carries_variation_id`, `test_each_lane_emits_six_fields_in_stable_order`, `test_field_legend_zh_emits_six_labels_in_stable_order` |
| MS-W8 — channel / account / publish_time / publish_url / publish_status / metrics_snapshot all surface | PASS | Six-field-stable-order test + per-field resolution / unresolved-fallback tests + closed-enum tests for publish_status |
| MS-W8 — read-only over closure (no schema widening) | PASS | `test_helper_never_touches_event_kinds_or_actor_kinds_or_channel_metrics_keys` (post-call invariant on the closure-contract closed sets); `test_publish_status_labels_zh_keys_match_closure_publish_status_values` (closed-enum mirror sanity check); `test_helper_does_not_mutate_closure` |
| MS-W8 — single truth path (no second truth source for publish state) | PASS | `test_backfill_helper_reads_same_closure_as_existing_pr3_block` (variation_id sets equal across `payload["matrix_script_publish_feedback_closure"]` and `payload["matrix_script_delivery_backfill"].lanes`) |
| MS-W8 — no invented publish state | PASS | Each per-field `STATUS_NOT_PUBLISHED` / `STATUS_NO_METRICS` / `STATUS_UNSOURCED` is a closed sentinel; no fallback synthesizes `published`. `test_publish_status_out_of_enum_degrades_gracefully` confirms out-of-contract values do not silently coerce. |
| MS-W8 — account-level semantics aligned with Matrix Script product-flow authority | PASS | Account is rendered as the closed `STATUS_UNSOURCED` tracked-gap row with operator-language explanation (`ACCOUNT_TRACKED_GAP_EXPLANATION_ZH`). `test_account_field_is_always_tracked_gap_even_when_published` confirms the gap is surfaced regardless of other-field resolution. |
| Hot Follow byte-isolation | PASS | No file under `gateway/app/services/hot_follow*` or template `hot_follow_*.html` modified; `task_publish_hub.html` Hot Follow / Baseline render paths bytewise unchanged; `test_hot_follow_payload_carries_neither_pr3_key` asserts behavioral isolation |
| Digital Anchor byte-isolation | PASS | No file under `gateway/app/services/digital_anchor/*` modified; `task_publish_hub.html` Digital Anchor `_da_kind == "digital_anchor"` block preserved verbatim; `test_digital_anchor_payload_carries_neither_pr3_key` asserts behavioral isolation |
| Asset Supply consumed read-only | n/a | No Asset Supply file touched (PR-3 does not consume Asset Supply) |
| No PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 / OWC-MS PR-2 truth modified | PASS | Forbidden-scope audit §7 below |
| Product-Flow Module Presence rule (ENGINEERING_RULES §13) — modules visible on `task_publish_hub.html` | PASS | Reviewer can read `gateway/app/templates/task_publish_hub.html` matrix_script branch and confirm: PR-U3 comprehension (preserved), Recovery PR-3 closure (preserved), MS-W7 copy_bundle (`data-role="matrix-script-delivery-copy-bundle"`), MS-W8 多渠道回填 (`data-role="matrix-script-delivery-backfill"`) |
| Test floor ≥30 cases per gate spec §5.2 | PASS | 78 active test cases shipped on Python 3.9 across two dedicated PR-3 test modules + 15 wiring cases on CI 3.10+ |

## 7. Forbidden-Scope Audit (against `owc_ms_gate_spec_v1.md` §4)

### §4.1 Truth-source / contract preservation
| Red line | Status |
| --- | --- |
| No Matrix Script packet truth mutation | clean — no packet schema or sample modified |
| No reopen of §8.A–§8.H correction chain | clean — no §8 artifact touched |
| No widening of `target_language`, canonical axes, or `source_script_ref` accepted-scheme set | clean — no scheme set or axis set modified |
| No operator-driven Phase B authoring | clean — PR-3 has no Phase B affordance; the 回填 view writes nothing |
| No `source_script_ref` repurposing | clean — helper never references `source_script_ref` |
| No new authoritative truth source for publishability | clean — PR-3 does not call `publish_readiness` directly; the 回填 view is purely closure-side |
| No second producer for `final_provenance` (L3) or L4 advisory | clean — neither field appears anywhere in the helpers |

### §4.2 Cross-line preservation
| Red line | Status |
| --- | --- |
| No Hot Follow file touched | clean |
| No Digital Anchor file touched | clean |
| No cross-cutting wiring change outside the existing `kind_value == "matrix_script"` / `_ms_kind == "matrix_script"` branches | clean — `task_view_helpers.py` edit confined to the existing `kind_value == "matrix_script"` branch; `task_publish_hub.html` edit confined to the existing `{% if _ms_kind == "matrix_script" %}` block (line 266–381) |

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
| No provider / model / vendor / engine controls or operator selector | clean — boundary tested recursively in both helper test modules + wiring test |
| No donor namespace import | clean — no `from swiftcraft.*` |
| No Asset Supply page / promote service / DAM expansion | clean |
| No React / Vite full rebuild or new component framework | clean — Jinja2 + minimal `data-role` attributes + plain JS only |
| No durable persistence backend swap | clean — closure store remains in-process; helpers consume read-only via `get_closure_view_for_task` |
| No bundling of MS-W* slices | clean — only MS-W7 + MS-W8 land here per the §5 PR slicing plan |

### §4.5 Closeout-paperwork independence
| Red line | Status |
| --- | --- |
| No forced advancement of prior closeout signoffs (recovery PR-1..PR-4 closeouts, Plan E phase closeouts, OWC-MS PR-1 / PR-2 closeouts) | clean — none touched. OWC-MS Closeout (the post-PR-3 paperwork-only PR) is intentionally NOT started in this PR per the user's mission |

## 8. Residual Risks

- **In-process closure store**: when the gateway process restarts, `feedback_closure_records[]` and `variation_feedback[]` reset to empty, so the multi-channel 回填 lanes reset too. Acceptable per Recovery Decision §4.3 (minimum operator capability, not durable persistence). A later wave may swap the in-process store for a durable backend without changing the closure shape or any of the two PR-3 helpers.
- **Per-account gap is explicit**: `account_id` is rendered as a tracked-gap row on every lane (closed `STATUS_UNSOURCED` sentinel). Operators see "尚未采集" + the explanation `ACCOUNT_TRACKED_GAP_EXPLANATION_ZH`. A future OWC scope (or a separate publish-account-capture wave) would land `account_id` on `variation_feedback[]` rows or `channel_metrics[]` snapshots; PR-3 names the gap rather than synthesizing a value.
- **Multi-account fan-out today**: if multiple accounts publish the same variation today, the contract's last-write-wins on `variation_feedback[i].publish_url / publish_status` means only the most recent account's state is rendered. The 回填 lane's `publish_event_count` reflects the cumulative event count, which serves as a hint but does not break out per-account state. This matches the contract's current design; per-account fanout is a future schema slicing item, not a PR-3 concern.
- **Publish-time string ordering**: `_latest_publish_time` sorts by lexicographic order of the `recorded_at` / `captured_at` string. ISO-8601 timestamps sort chronologically under lexicographic order, so this is correct for any timestamp the closure router accepts today. If a non-ISO timestamp ever lands on a record, the helper degrades gracefully (the `channel_metrics_captured_at` fallback is independently sourced).
- **MS-W7 outline contract gap**: today's `task["config"]["entry"]` does not carry the structural Hook / Body / CTA fields — only `topic / target_platform / audience_hint / tone_hint / length_hint`. The MS-W7 helper exposes the four operator-language Delivery Center subfields with per-subfield `STATUS_UNRESOLVED` fallback citing the future Outline Contract per product-flow §9.2. When the contract lands, the helper's per-subfield projection can switch from the sentinel to the real value with no template change.
- **Forbidden-token scrub may shadow legitimate text**: the validator R3 scrub matches `vendor / model_id / provider / engine` as case-insensitive substrings. A legitimate operator-supplied caption containing one of those words (e.g., a literal English noun "vendor") would be scrubbed to empty and the subfield would render `STATUS_UNRESOLVED`. The PR-3 helper inherits this discipline from PR-2 (which uses the same scrub list) and the OWC-MS gate spec §4.4 ("No provider/model/vendor/engine controls or operator selector"). A future scrub refinement would tighten the match (e.g., regex word-boundary instead of substring) but is out of OWC-MS PR-3 scope.
- **Branch / PR stacking hygiene**: this PR is built on the worktree branch `claude/adoring-herschel-4761b5` rebased onto `origin/main` (which carries OWC authority normalization #121, OWC-MS PR-1 #122, OWC-MS PR-2 #123, and post-merge housekeeping #124 — confirmed at `git log --oneline -5`). The PR diff contains only PR-3 files; no prior-PR commits are bundled.
- **Wiring test runs only on CI 3.10+**: the 15-case wiring test module imports `publish_hub_payload`, which transitively imports `gateway.app.config:43` — a pre-existing Python 3.9 PEP-604 limitation documented across PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 / OWC-MS PR-2 logs. Local runs on 3.9 auto-skip the wiring tests; CI on 3.10+ exercises the full set. Not a regression introduced by PR-3.

## 8.1 Reviewer-Fail Correction Pass (2026-05-05)

The first OWC-MS PR-3 revision returned FAIL with two blockers:

1. **MS-W7 was acting as a second copy producer.** The first revision synthesized `cta` from `entry.target_platform` and `comment_keywords` from `entry.audience_hint` + `entry.tone_hint`. Adjacent task-entry hints are NOT publish-copy truth — they are Phase A authoring hints that drive Phase B variation cells, not publish copy. Synthesizing copy_bundle subfields from those hints made the helper a second authoritative copy producer (gate spec §4.1 violation).
2. **PR-3 wiring tests depended on ambient storage configuration.** The first revision drove the attach path through `publish_hub_payload(task)`, which transitively imports `gateway.app.config` (PEP-604 baseline) and calls `compute_composed_state` → `artifact_storage.object_exists` (ambient storage probe). The wiring tests auto-skipped on Python 3.9 by `pytestmark = pytest.mark.skipif`, which the reviewer correctly rejected ("Do not solve this by skipping the test or reducing coverage").

### 8.1.1 Exact code-path corrections

- **MS-W7 single-source discipline** (`gateway/app/services/matrix_script/delivery_copy_bundle_view.py`):
  - Removed all reads of `task["config"]["entry"]` from the helper. The task is consumed only for the `kind == "matrix_script"` check; no `topic` / `target_platform` / `audience_hint` / `tone_hint` / `length_hint` is consumed.
  - Each subfield now has exactly one authorized source on the existing publish-hub `copy_bundle` projection:
    - `title` ← `base_copy_bundle.caption`
    - `hashtags` ← `base_copy_bundle.hashtags`
    - `cta` ← `base_copy_bundle.comment_cta`
    - `comment_keywords` → ALWAYS `STATUS_UNRESOLVED` (no producer in `copy_bundle` today)
  - When the authoritative source is empty, the subfield falls back to the closed `STATUS_UNRESOLVED` sentinel with operator-language explanation citing the future copy projection contract per product-flow §7.1 + §9.5 Deliverable Contract.
  - Per-subfield UNRESOLVED fallback discipline preserved verbatim — never panel-wide replacement.
  - The `cta` and `comment_keywords` UNRESOLVED explanations explicitly name the prohibition on synthesizing from `target_platform` / `audience_hint` / `tone_hint` so reviewers can trace the Blocker 1 discipline from the rendered card.
  - **No second authoritative producer for publish copy. No packet truth mutation. No contract redesign.**
- **PR-3 wiring seam extraction** (`gateway/app/services/matrix_script/publish_hub_pr3_attach.py` — new):
  - The OWC-MS PR-3 attach block in `task_view_helpers.py::publish_hub_payload` was extracted into a thin, importable seam `attach_matrix_script_delivery_pr3_extras(*, payload, task)`.
  - The seam imports nothing from `gateway.app.config`; nothing from `artifact_storage`; nothing that requires Python 3.10+ syntax. It calls only `derive_matrix_script_delivery_copy_bundle` + `derive_matrix_script_delivery_backfill` — both pure projections.
  - `publish_hub_payload` was updated to import and invoke this same seam — production behavior is byte-equivalent to the prior inline block (verified by source-import binding test + adjacent regression).
- **Wiring test rewritten** (`gateway/app/services/tests/test_matrix_script_publish_hub_pr3_wiring.py`):
  - All `pytest.mark.skipif` on Python 3.9 removed.
  - Test calls `attach_matrix_script_delivery_pr3_extras(payload=skeleton, task=task)` directly with hand-built payload skeletons that mirror the publish-hub state at the moment the inline attach block runs in production.
  - **Production binding** is verified by `test_publish_hub_payload_invokes_the_pr3_attach_seam`: reads the source bytes of `task_view_helpers.py` and asserts (a) the seam import statement is present, (b) the seam invocation is present, (c) the call is positioned after the `kind_value == "matrix_script"` branch entry. This proves the seam is wired into production without importing `task_view_helpers.py` (which would trigger the `gateway.app.config` PEP-604 chain).
  - **Behavior coverage is preserved**: matrix_script attach with initialized empty closure (lanes × variation_id, fields all unresolved/unsourced/pending), matrix_script attach with published closure events (publish_url + publish_status + channel + metrics_snapshot resolve), Hot Follow / Digital Anchor / Baseline cross-line isolation, single-truth invariant for closure consumption, validator R3 forbidden-token recursive walk, Blocker 1 invariant assertions (caption-only resolution, all-unresolved when only entry hints present), defense-in-depth on malformed inputs, no input mutation, seam signature contract.

### 8.1.2 Tests after correction

- `test_matrix_script_delivery_copy_bundle_view.py` — **40/40 PASS** on Python 3.9 (added Blocker 1 invariants: `test_title_unresolved_when_caption_empty_even_if_topic_present`, `test_cta_unresolved_when_target_platform_present_but_comment_cta_empty`, `test_comment_keywords_always_unresolved_regardless_of_inputs`, `test_adjacent_entry_hints_alone_produce_all_unresolved_subfields`, `test_individual_entry_hint_does_not_resolve_any_subfield` × 5 hint fields, `test_blocker_1_explanations_explicitly_name_hint_prohibition`).
- `test_matrix_script_delivery_backfill_view.py` — **40/40 PASS** (unchanged from first revision; MS-W8 already complied).
- `test_matrix_script_publish_hub_pr3_wiring.py` — **22/22 PASS** on Python 3.9 (was 0 PASS / 16 SKIPPED). Active cases on the actual attach path: matrix_script-with-initialized-empty-closure lane assertion, matrix_script-with-published-closure resolution, Hot Follow / Digital Anchor / Baseline isolation × 3, single-truth-closure invariant, validator R3 recursive walk × 4, Blocker 1 caption-only assertion, Blocker 1 all-unresolved-from-entry-hints assertion, defense-in-depth × 2, production-binding source check, no-mutation, seam-signature-contract.

**Subtotal after correction: 102/102 PASS** on Python 3.9 (40 + 40 + 22 across three dedicated PR-3 modules). Gate spec §5.2 ≥30 floor: PASS (102 cases, 3.4× the floor).

Adjacent regression unchanged: **484 PASS / 6 SKIPPED / 0 FAIL** (the 6 skips are the pre-existing `test_matrix_script_review_zone_submit_http.py` HTTP cases auto-skipping on Python 3.9 per the documented baseline — not introduced by PR-3).

**Aggregate after correction: 586 PASS / 6 SKIPPED / 0 FAIL** on Python 3.9 (102 PR-3 + 484 adjacent).

### 8.1.3 Why each FAIL item is now closed

| FAIL item | Closed by |
| --- | --- |
| (1) MS-W7 was acting as a second copy producer | Helper rewritten with single-source discipline per subfield: `caption` → title; `hashtags` → hashtags; `comment_cta` → cta; comment_keywords always UNRESOLVED. Helper no longer reads `task["config"]["entry"]` for any subfield value. Asserted by `test_title_unresolved_when_caption_empty_even_if_topic_present`, `test_cta_unresolved_when_target_platform_present_but_comment_cta_empty`, `test_comment_keywords_always_unresolved_regardless_of_inputs`, `test_adjacent_entry_hints_alone_produce_all_unresolved_subfields`, and the parametric `test_individual_entry_hint_does_not_resolve_any_subfield` covering all five entry hints. |
| (2) PR-3 wiring tests depended on ambient storage configuration | Attach path extracted into `gateway/app/services/matrix_script/publish_hub_pr3_attach.py` — a pure seam with zero `gateway.app.config` / `artifact_storage` dependency. Wiring test imports the seam directly and exercises the actual attach path against hand-built payload skeletons. All `pytest.mark.skipif` removed. Production binding is independently verified by reading `task_view_helpers.py` source bytes (`test_publish_hub_payload_invokes_the_pr3_attach_seam`). 22/22 PASS on Python 3.9 native, no skips, no reduced coverage. |

### 8.1.4 Residual risks after correction

- The 6 `test_matrix_script_review_zone_submit_http.py` HTTP-side cases continue to auto-skip on Python 3.9 due to the **pre-existing repo baseline** (`gateway/app/config.py:43` PEP-604 union; documented across PR-1 / PR-2 / PR-3 / PR-4 / OWC-MS PR-1 / OWC-MS PR-2 logs). Not introduced by PR-3. CI on Python 3.10+ runs them.
- All other residual risks from §8 carry forward unchanged.

## 8.2 Post-Review Codex P1 Correction (2026-05-05)

A second post-§8.1 review surfaced one remaining Codex P1 thread on `gateway/app/services/matrix_script/delivery_backfill_view.py:512`: when a Matrix Script task had no closure yet, the helper returned `{}` and the JS renderer hid the entire backfill card — operators never saw the intended "尚未生成 closure 记录" empty-state message, and any consumer indexing `backfill["lane_count"]` / `"lanes"` / `"is_matrix_script"` would `KeyError`.

### 8.2.1 Exact code-path correction

- **`delivery_backfill_view.py`**: when `closure` is `None` or an empty mapping, the helper now emits the matrix_script-shaped bundle with zero lanes — `is_matrix_script=True` + `panel_title_zh` + `panel_subtitle_zh` + `field_legend_zh` (six labels) + `lanes=[]` + `lane_count=0` + `tracked_gap_summary_zh` naming the "尚未生成 closure" empty-state. A non-matrix_script closure (cross-line wiring bug) still returns `{}` so cross-line render stays untouched.
- **`publish_hub_pr3_attach.py`**: cross-line isolation moved into the seam itself. When the seam is invoked with a non-matrix_script task (caller bug; production publish_hub_payload still gates externally), both PR-3 keys are written as `{}` so non-matrix_script payloads stay untouched. Helpers can now assume matrix_script context.
- **Tests**: `test_returns_zero_lanes_panel_for_none_closure`, `test_returns_zero_lanes_panel_for_empty_mapping`, `test_no_closure_panel_carries_documented_keys_so_template_renders` cover the helper. `test_matrix_script_with_none_closure_emits_zero_lanes_panel`, `test_attach_with_malformed_closure_does_not_raise_and_emits_zero_lanes_panel` cover the seam. Cross-line isolation tests still assert `{}` for Hot Follow / Digital Anchor / Baseline kinds at the seam.

### 8.2.2 Tests after correction

- `test_matrix_script_delivery_copy_bundle_view.py` — **40/40 PASS**.
- `test_matrix_script_delivery_backfill_view.py` — **41/41 PASS** (added Codex P1 invariant tests).
- `test_matrix_script_publish_hub_pr3_wiring.py` — **22/22 PASS** native on Python 3.9.
- **Subtotal: 103/103 PASS** dedicated PR-3.
- Adjacent regression unchanged: **484 PASS / 6 SKIPPED / 0 FAIL**.
- **Aggregate: 587 PASS / 6 SKIPPED / 0 FAIL** on Python 3.9.

### 8.2.3 Why the Codex thread is now closed

The helper now structurally guarantees the documented bundle shape for the most common pre-publish state (no closure yet); the JS renderer always has `is_matrix_script == true` to gate on, the panel is shown, and the empty-state message at `data-role="ms-delivery-backfill-empty"` renders. Consumers indexing `backfill["lane_count"]` will get `0` instead of `KeyError`. The cross-line isolation that the original `closure → {}` short-circuit was guarding is now enforced at the seam (kind check) instead, which keeps it from leaking to the post-init "no closure yet" case. The Codex review thread was resolved on PR #125 with this fix in place.

## 9. Exact Statement of What Remains for the Next PR

OWC-MS Closeout — aggregating audit + signoff per `owc_ms_gate_spec_v1.md` §6 + §10. Records MS-A1..MS-A8 PASS:

- MS-A1 — OWC-MS PR-1 (MS-W1 + MS-W2) implementation green + merged ✅ (PR #122 / `0b23605`)
- MS-A2 — OWC-MS PR-2 (MS-W3..W6) implementation green + merged ✅ (PR #123 / `c7a5a89`)
- MS-A3 — OWC-MS PR-3 (MS-W7 + MS-W8) implementation green + merged ⏳ (this PR, opening pending)
- MS-A4 — Hot Follow baseline preserved (golden-path live regression — coordinator confirmation block in closeout)
- MS-A5 — Digital Anchor freeze preserved per PR (per-PR forbidden-scope audit referenced in closeout)
- MS-A6 — §4 forbidden-scope audit (full pass on §4.1–§4.5 across PR-1 + PR-2 + PR-3)
- MS-A7 — OWC-MS Closeout signoff (Architect Raobin + Reviewer Alisa + Coordinator Jackie + Product Manager)
- MS-A8 — Product-Flow Module Presence rule (ENGINEERING_RULES §13) verified for each MS-W* slice (reviewer walks `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Matrix Script blocks and confirms each module renders)

OWC-MS Closeout opens **after** OWC-MS PR-3 merges + reviews. The user mission for this session explicitly stops here ("Stop after opening OWC-MS PR-3. Do not start OWC-MS Closeout.").

## 10. References

- Gate spec: `docs/reviews/owc_ms_gate_spec_v1.md` §3 MS-W7 + MS-W8; §4 forbidden; §5.1 file isolation; §5.2 ≥30 test floor; §6 MS-A1..MS-A8; §7 freezes; §9 R1..R5
- Sister-phase gate spec: `docs/reviews/owc_da_gate_spec_v1.md` (entry condition DA-E3 will require this PR's closeout chain)
- Predecessor docs PR: `docs/execution/APOLLOVEO_2_0_OWC_AUTHORITY_GATE_NORMALIZATION_EXECUTION_LOG_v1.md`
- Predecessor implementation PRs: `docs/execution/APOLLOVEO_2_0_OWC_MS_PR1_TASK_AREA_EXECUTION_LOG_v1.md`, `docs/execution/APOLLOVEO_2_0_OWC_MS_PR2_WORKBENCH_FIVE_PANEL_EXECUTION_LOG_v1.md`
- Engineering rule binding: `ENGINEERING_RULES.md` §13 Product-Flow Module Presence
- Line-specific authority: `docs/product/matrix_script_product_flow_v1.md` §7.1 / §7.2 / §7.3
- Recovery PR-1 (publish_readiness producer): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`
- Recovery PR-3 (Matrix Script closure binding): `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md`
- Closure contract (read-only consumer): `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` (with the OWC-MS PR-2 §"Operator review zone tag (additive)" addendum already merged on 2026-05-05)
