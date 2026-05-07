# Matrix Script Result-Oriented UI — Implementation Slicing v1

Date: 2026-05-07
Status: **Design package only.** Recommended PR slicing for a future Matrix Script Result-Oriented UI Implementation Wave that consumes the design package frozen in [matrix_script_result_oriented_ui_plan_v1.md](matrix_script_result_oriented_ui_plan_v1.md), [matrix_script_task_area_wireframe_v1.md](matrix_script_task_area_wireframe_v1.md), [matrix_script_workbench_wireframe_v1.md](matrix_script_workbench_wireframe_v1.md), [matrix_script_delivery_center_wireframe_v1.md](matrix_script_delivery_center_wireframe_v1.md). This addendum extends those four files; it does not replace any of them. **It does not open the implementation gate.**

Authority of creation: same as the result-oriented UI plan §0. Bound by [matrix_script_result_oriented_ui_plan_v1.md §13](matrix_script_result_oriented_ui_plan_v1.md). When this addendum conflicts with any underlying authority — product, contract, surface, wave, alignment map — the underlying authority wins.

This document does **not** mutate any contract / schema / sample / template / test / runtime, does **not** touch Hot Follow / Digital Anchor / Asset Supply files, does **not** open any implementation gate. The frozen next engineering sequence in [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7 remains in force unchanged.

---

## 1. What this addendum is and is not

### 1.1 Is

- A binding-and-exhaustive PR slicing for the future Result-Oriented UI Implementation Wave (working name: **OWC-MS-RO**, reusing the OWC-MS / Recovery Wave precedent for naming and signoff cadence).
- For each PR slice: the operator-visible outcome it ships, the backend/runtime feeds it consumes, what remains as secondary diagnostics only, the acceptance evidence required for it to merge, and the hard non-goals it must respect.
- The Closeout shape (acceptance rows + signoff block) for the wave as a whole.
- A reading-declaration template for any future implementation PR that opens against this slicing.

### 1.2 Is not

- Not a wave gate spec. The actual gate spec for this future wave (parallel to [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md), [docs/reviews/owc_da_gate_spec_v1.md](../reviews/owc_da_gate_spec_v1.md), [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md)) MUST be authored separately — under whatever wave authority is current when the alignment map's frozen sequence reaches this step — before any PR-1 may open.
- Not a contract. It does not author or mutate any contract. It does not widen any closed enum.
- Not authority to bypass the alignment map's frozen next engineering sequence. The wave that opens this slicing is gated on prior steps closing, **not** on this addendum merging.
- Not implementation guidance ("write the helper this way"). It is sequencing guidance ("this PR ships these blocks; the next PR ships those blocks").

---

## 2. Pre-conditions for opening this implementation wave

The wave that consumes this slicing MUST NOT open until **all** of the following land:

1. The follow-on Matrix Script trial re-entry review (docs-only, separate PR per alignment map §7 step 7) is authored AND §8 four-party signoff merges.
2. Plan A live-trial Matrix Script execution runs against §7.1 samples 3 / 4 / 5 (Matrix Script `mm` / `vi` / post-§8.F) plus the Matrix Script portion of sample 6.
3. Matrix Script live-trial findings + four-party signoff are recorded.
4. A new gate spec for this wave (working name: **owc_ms_ro_gate_spec_v1.md** under `docs/reviews/`) is authored, observing recovery amendment §7 hard boundaries (no new contracts, no new structural surface modules, no closed-enum widening, no Hot Follow / Digital Anchor / Asset Supply touch) AND its §10 architect (Raobin) + reviewer (Alisa) signoff merges.

If any of the above is not yet in place, this slicing remains **paper only**. PR-1 below MUST NOT open.

The wave that opens this slicing is BLOCKED on:

- Platform Runtime Assembly Wave (Capability Expansion is gated on Platform Runtime Assembly signoff per alignment map §7.5; this UI implementation wave is allowed to land before Platform Runtime Assembly because it is pure presentation-layer over already-frozen substrate, mirroring the Recovery Wave's relation to Platform Runtime Assembly — **but** that allowance is conditional on the gate spec authored under (4) above explicitly placing this wave inside the alignment map's sequence; it is not a unilateral decision of this addendum).

---

## 3. Slicing rationale

### 3.1 Why four PRs in this order

The four-PR shape mirrors three established precedents on this line:

| Wave | Slicing | Pattern |
|---|---|---|
| OWC-MS | PR-1 (MS-W1+W2 Task Area) → PR-2 (MS-W3..W6 Workbench) → PR-3 (MS-W7+W8 Delivery+Publish) → Closeout | surface-by-surface |
| OWC-DA | PR-1 (DA-W1+W2 Task Area) → PR-2 (DA-W3..W7 Workbench) → PR-3 (DA-W8+W9 Delivery+Publish) → Closeout | surface-by-surface |
| Recovery Wave | RC PR-1 (RC-R6 summary) → RC PR-2 (RC-R1+R2+R3 script+variants) → RC PR-3 (RC-R4 next-action) → RC PR-4 (RC-R5+R7+R8 delivery package + publish/backfill) → Closeout | result-discipline-by-discipline |

This addendum follows the surface-by-surface shape (OWC-MS / OWC-DA precedent) because the result-oriented UI is fundamentally a *re-arrangement of surfaces*, not a new substrate landing. The Recovery Wave's discipline-by-discipline shape was right for its mission (each RC-R* delivered a new helper module); for this wave the helpers already exist, so the natural slice axis is *which surface gets re-organised*.

### 3.2 Why split Workbench into two PRs

The Workbench wireframe defines six blocks A–F. Splitting into PR-2 (Blocks A / B / C — read-side comprehension) and PR-3 (Blocks D / E / F — action-side review) preserves three properties:

1. **Single-PR review-comprehension boundary.** A reviewer can audit "does the operator now read the goal and structure correctly" (PR-2) independently from "does the operator now act on candidate review correctly" (PR-3). Mixing them produces a too-large diff that resists per-block byte-isolation audit.
2. **Action affordances land last.** PR-3 is the only PR in this wave that introduces operator-initiated actions (regenerate scoped per cell_id wiring; submit zone-scoped review form). Landing those after read-side comprehension is the same risk-ordering OWC-MS PR-2 used (closure submit affordance landed late in the slice).
3. **Block-F delivery-teaser dependency on PR-4.** Block F is a *teaser* of the Delivery Center, so it must render the same `compute_publish_readiness` truth as Block F of the Delivery Center. Landing both in the same wave (PR-3 + PR-4) keeps that consistency under the same review window.

### 3.3 Why Delivery Center + Publish Feedback together

Delivery Center Blocks A–F and Publish Feedback (which is Block E of the Delivery Center wireframe) live on the same template (`task_publish_hub.html`) and share the same closure-D.1 endpoint. Splitting them across two PRs would introduce a window where Delivery Center renders but Publish Feedback is still on the old shell — a worse operator experience than landing them together.

### 3.4 Why a separate Closeout

Aggregating audit + signoff across PR-1..PR-4 follows OWC-MS / OWC-DA / Recovery Wave precedent. The Closeout is documentation-only and gates the wave's external claim of completion.

---

## 4. PR-1 — Task Area card refit

### 4.1 Operator-visible outcome

The Matrix Script Task Area card in `gateway/app/templates/tasks.html` becomes the production-management card defined by [matrix_script_task_area_wireframe_v1.md §4](matrix_script_task_area_wireframe_v1.md):

- Card body renders the binding-and-exhaustive nine fields (subject / line marker / stage badge / result pill / variant count / publishable count / current best candidate / current blocker / latest generation time).
- A next-action chip below the card body renders an operator-language sentence ("下一步: …").
- A three-button row at the bottom of the card exposes "打开工作台" / "打开交付中心" / "打开发布反馈" (closes interaction gap IG-1).
- The three-tier lane projection (script / variant / publish) drives a single active-lane highlight per card.
- Result-pill / blocker-line text is operator-language only; no raw English `head_reason` enum.
- Stage and result filters at the page header use the closed `STAGE_*` and `STATUS_*` operator-label sets.

### 4.2 Backend / runtime feeds consumed

| UI element | Service | File |
|---|---|---|
| Card body 8 fields | `derive_matrix_script_task_card_summary` | gateway/app/services/matrix_script/task_card_summary.py |
| Stage badge | `derive_matrix_script_eight_stage_state` | gateway/app/services/matrix_script/task_area_convergence.py |
| Three-tier lanes | `derive_matrix_script_three_tier_lanes` | gateway/app/services/matrix_script/task_area_convergence.py |
| Result pill / next-action chip | `derive_matrix_script_task_area_result_status` | gateway/app/services/matrix_script/result_status_view.py |
| Operator-language label dictionary | `HEAD_REASON_LABELS_ZH` | publish_readiness producer (Recovery PR-1 substrate) |
| Open-workbench route | `/tasks/{id}` | gateway/app/routers/tasks.py (existing) |
| Open-delivery route | `/tasks/{id}/publish-hub` | gateway/app/routers/tasks.py (existing) |
| Open-publish-feedback anchor | `/tasks/{id}/publish-hub#publish-feedback` | template anchor (existing) |

All consumed feeds already exist on `main` (Recovery Wave + OWC-MS substrate). PR-1 introduces no new helper module.

### 4.3 Secondary diagnostics only (out of scope for the operator surface)

- Validator drawer link.
- Ref counters (`generic_refs.length`, `line_specific_refs.length`).
- `cell_id` / `slot_id` / axis-tuple raw labels.
- Per-variant inspector pane (engineering inspector remains accessible behind a non-operator route, untouched by this PR).

### 4.4 Acceptance evidence

| ID | Evidence |
|---|---|
| RO-1.1 | Matrix Script branch of `tasks.html` renders the nine binding-and-exhaustive card fields per [matrix_script_task_area_wireframe_v1.md §4](matrix_script_task_area_wireframe_v1.md); diff cited per field. |
| RO-1.2 | Next-action chip + three-button row render exactly as wireframe §4.1 + §4.2; "打开发布反馈" button is present and routes to the publish-hub `#publish-feedback` anchor. |
| RO-1.3 | Hot Follow card branch (`kind == "hot_follow"`) and Digital Anchor card branch (`kind == "digital_anchor"`) bytewise unchanged; cited via `git diff --stat HEAD~1 HEAD` showing zero line touch in those template ranges. |
| RO-1.4 | Test floor: ≥ 30 dedicated test cases in a new `gateway/app/services/tests/test_matrix_script_task_area_card_refit.py` (mirrors recovery gate spec §5.2 floor for surface refits). |
| RO-1.5 | Adjacent regression: Matrix Script-touching test files all PASS; cross-line preservation tests for Hot Follow + Digital Anchor card branches PASS. |
| RO-1.6 | No new endpoint, no new closed-enum widening, no contract / schema / sample / packet / validator change. |
| RO-1.7 | Coordinator confirmation block placeholder for Hot Follow golden-path live regression (filled at Closeout). |

### 4.5 Hard non-goals

- No changes to the `/tasks/matrix-script/new` intake page (intake design is owned by [docs/design/surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md), not by this wave).
- No changes to non-Matrix-Script card branches (`kind == "hot_follow"` and `kind == "digital_anchor"` remain bytewise unchanged).
- No vendor / model / provider / engine column or filter on this surface.
- No raw `cell_id` / `slot_id` / `content://` handle in card body or filters.
- No archive iteration-hint trailer (PG-4 deferred to a presenter-only follow-on PR; out of scope here).
- No "duplicate as new task" affordance (IG-3 deferred to a future Plan E phase).
- No reference badge (`hot_follow ✓`) on Matrix Script card (PG-5 deferred; trivial template addition that does not gate this PR).

---

## 5. PR-2 — Workbench Blocks A / B / C (read-side comprehension)

### 5.1 Operator-visible outcome

The Matrix Script branch of `gateway/app/templates/task_workbench.html` is re-organised so Blocks A / B / C from [matrix_script_workbench_wireframe_v1.md](matrix_script_workbench_wireframe_v1.md) render in document order at the top of the panel, **above** the existing Phase B Variation Panel (which is preserved verbatim as secondary diagnostics):

- **Block A — Goal Summary**: header / 任务身份 / 当前总状态 / 当前阻塞 / 下一步 + jump buttons (前往交付中心 / 前往发布反馈).
- **Block B — Script Structure**: Hook / Body / CTA / 关键词 / 禁用词 in operator-readable form.
- **Block C — Variant Strategy**: per-variant differentiator table (语气 / 受众 / 节奏 / 视觉 / 字幕配音), one row per `cells[]`, with why-this-variant tooltip on hover.

Operator language is enforced; no `slot_id` / `cell_id` / axis-tuple raw labels appear in any of the three blocks.

### 5.2 Backend / runtime feeds consumed

| Block | Service | File |
|---|---|---|
| A — Goal Summary | `derive_matrix_script_workbench_comprehension` + `derive_matrix_script_workbench_result_summary` | gateway/app/services/matrix_script/workbench_comprehension.py + result_status_view.py |
| A — Stage badge | `derive_matrix_script_eight_stage_state` | gateway/app/services/matrix_script/task_area_convergence.py |
| B — Script Structure | `derive_matrix_script_script_structure_view` | gateway/app/services/matrix_script/script_structure_view.py |
| C — Variant Strategy | `derive_matrix_script_readable_variants` (axis-tuple → operator label) | gateway/app/services/matrix_script/readable_variant_view.py |
| C — Variant count | `derive_matrix_script_workbench_comprehension.variant_summary` | gateway/app/services/matrix_script/workbench_comprehension.py |

All feeds already exist (Recovery Wave PR-2 + workbench comprehension PR-U2 substrate). PR-2 introduces no new helper module.

### 5.3 Secondary diagnostics only (preserved verbatim)

- Existing Phase B Variation Panel — Axes table, Cells × Slots table, Slot detail expand, Attribution refs — preserved verbatim **below** Blocks A / B / C, mirroring the additive convention OWC-MS PR-U2 used. The panel remains the engineer-facing inspector for axis-tuple raw structure.
- Existing comprehension block (PR-U2 four-zone alignment summary) preserved verbatim.

### 5.4 Acceptance evidence

| ID | Evidence |
|---|---|
| RO-2.1 | Matrix Script branch of `task_workbench.html` renders Blocks A / B / C in document order at the top of the panel per [workbench wireframe §3 / §4 / §5](matrix_script_workbench_wireframe_v1.md). |
| RO-2.2 | Block A header surfaces operator-language status / blocker / next-action; no raw English `head_reason` enum string appears. |
| RO-2.3 | Block B renders Hook / Body / CTA / keywords / forbidden-terms with no `slot_id` / `cell_id` / `content://` handle leakage; presenter dereferences server-side. |
| RO-2.4 | Block C variant table has the six operator-language columns; `axis_id`, `axis-tuple` raw labels, `script_slot_ref`, `binds_cell_id` MUST NOT appear in this block. |
| RO-2.5 | Phase B Variation Panel preserved verbatim below the new blocks; cited via `git diff` showing zero deletion in the panel block. |
| RO-2.6 | Hot Follow + Digital Anchor workbench branches bytewise unchanged. |
| RO-2.7 | Test floor: ≥ 35 dedicated test cases across `test_matrix_script_workbench_blocks_a_b_c.py` (or per-block split files). |
| RO-2.8 | Adjacent regression: matrix_script-touching workbench test set PASS; cross-line preservation tests PASS. |
| RO-2.9 | No new endpoint, no contract / schema / packet / validator change. |

### 5.5 Hard non-goals

- No operator-driven Phase B authoring (`axes[]` / `cells[]` / `slots[]` authoring) — forbidden by Plan E gate spec §4.3 + recovery amendment §7.
- No closed-enum widening on `axis_kind_set`, `slot_kind_set`, `REVIEW_ZONE_VALUES`.
- No axis-tuple raw labels in Block C (PG-2 partially closes via the readable_variants axis-tuple dictionary; further axis-kind coverage is presenter-only follow-on).
- No vendor / model / provider / engine label in any block.
- No closure-event posting from Blocks A / B / C (closure-D.1 affordances land in PR-3 only).
- No removal of the Phase B Variation Panel; the panel is preserved verbatim as secondary diagnostics.

---

## 6. PR-3 — Workbench Blocks D / E / F (action-side review)

### 6.1 Operator-visible outcome

The Matrix Script branch of `task_workbench.html` is extended to render Blocks D / E / F from the workbench wireframe **below** Blocks A / B / C (PR-2's substrate) and **above** the preserved Phase B Variation Panel:

- **Block D — Generate / Regenerate**: primary "生成 N 个变体" + secondary "重新生成被阻塞的变体 (M)" actions; precondition list; blocker-reason operator label; no provider/model selector.
- **Block E — Candidate Review**: per-variant card with preview slot, subtitle / audio / package status, QC three-item checks, four review-zone chips (`REVIEW_ZONE_VALUES`), recommended ⭐ marker, three actions (选定推荐 / 提交分区评审 / 重新生成此变体).
- **Block F — Delivery Teaser**: publish-gate banner + required-deliverable lane summary + `scene_pack` non-blocking note + "前往交付中心" jump button.

Block E's "提交分区评审意见" form posts to the existing `POST /api/matrix-script/closures/{task_id}/events` endpoint with `event_kind == "operator_note"` + optional `review_zone ∈ REVIEW_ZONE_VALUES`. No closed-enum widening.

### 6.2 Backend / runtime feeds consumed

| Block | Service / endpoint | File |
|---|---|---|
| D — Recommended action / preconditions | `derive_matrix_script_recommended_action` | gateway/app/services/matrix_script/recommended_action_view.py |
| D — Blocker label | `compute_publish_readiness.head_reason` → `HEAD_REASON_LABELS_ZH` | publish_readiness producer (Recovery PR-1 substrate) |
| D — Primary / secondary action wiring | existing variation execution path inside `wiring.build_operator_surfaces_for_workbench` (matrix_script branch) | gateway/app/services/operator_visible_surfaces/wiring.py |
| E — Per-variant preview compare | `derive_matrix_script_preview_compare_view` | gateway/app/services/matrix_script/preview_compare_view.py |
| E — Subtitle / audio / package status | `derive_matrix_script_qc_diagnostics_view` + `derive_matrix_script_delivery_ready_package` | gateway/app/services/matrix_script/qc_diagnostics_view.py + delivery_ready_package_view.py |
| E — Review-zone chips | `derive_matrix_script_review_zone_view` | gateway/app/services/matrix_script/review_zone_view.py |
| E — Submit-review form | `POST /api/matrix-script/closures/{task_id}/events` (existing endpoint; closed `D1_EVENT_KINDS` + `REVIEW_ZONE_VALUES`) | gateway/app/routers/matrix_script_closure.py + publish_feedback_closure.py |
| F — Publish gate teaser | `compute_publish_readiness` | publish_readiness producer (Recovery PR-1 substrate) |
| F — Required deliverable lane summary | `derive_matrix_script_delivery_comprehension` | gateway/app/services/matrix_script/delivery_comprehension.py |
| F — Scene_pack non-blocking | `SCENE_PACK_BLOCKING_ALLOWED = False` | gateway/app/services/matrix_script/delivery_binding.py |

All feeds already exist. PR-3 introduces no new helper module and no new endpoint.

### 6.3 Secondary diagnostics only (preserved verbatim)

- Existing Phase B Variation Panel preserved verbatim below Blocks D / E / F.
- Existing closure-D.1 inspector paths (engineering-facing) untouched.
- Existing per-variant final-media engineering view (when present) untouched.

### 6.4 Acceptance evidence

| ID | Evidence |
|---|---|
| RO-3.1 | `task_workbench.html` Matrix Script branch renders Blocks D / E / F in document order below Blocks A / B / C per [workbench wireframe §6 / §7 / §8](matrix_script_workbench_wireframe_v1.md). |
| RO-3.2 | Block D primary action label reads "生成 N 个变体" with N from `derive_matrix_script_workbench_comprehension.variant_summary.count`; secondary label reads "重新生成被阻塞的变体 (M)" with M from `RECOMMENDED_BUCKET_BLOCKED` aggregate count. |
| RO-3.3 | Block E per-variant card renders preview-slot (tracked-gap or final-media handle), subtitle / audio / package status pills, QC three-item checks, four review-zone chips, recommended ⭐ marker, three action buttons. |
| RO-3.4 | Block E "提交分区评审意见" form posts to `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_note"` + (optional) `review_zone ∈ REVIEW_ZONE_VALUES` ONLY; no enum widening; no new endpoint. |
| RO-3.5 | Block F publish-gate banner consumes `compute_publish_readiness` directly; no second-source `publishable` derivation (RC-A7). |
| RO-3.6 | Audit: zero `final_video` / `publish_url` synthesis even under adversarial empty-state input (RC-R8). |
| RO-3.7 | Hot Follow + Digital Anchor workbench branches bytewise unchanged. |
| RO-3.8 | Test floor: ≥ 50 dedicated test cases across PR-3 service / template / closure-event suites (mirrors OWC-DA PR-2 floor for multi-block workbench landings). |
| RO-3.9 | Adjacent regression: closure-D.1 endpoint test suite PASS; cross-line preservation tests PASS. |
| RO-3.10 | No new endpoint, no contract / schema / packet / validator change, no new closed-enum widening. |

### 6.5 Hard non-goals

- No per-variant `cell_id` execution dispatch for "重新生成此变体" (IG-2 deferred to a future presenter-only PR — current wiring scopes to bulk regeneration; per-variant scoping requires a thin presenter-side dispatch which is out of scope here unless the gate spec referenced in §2 (4) explicitly authorises it).
- No closure-D.1 enrichment for "选定为推荐版本" state transition (IG-4 deferred — current behaviour is `operator_note`-only; a future closure-D.1 enrichment may add an explicit `record_kind` for "selected as recommended" without enum widening on `D1_EVENT_KINDS`).
- No advisory strip in Block E (BG-1 — L4 advisory producer not yet emitting).
- No inline `final_video` player (IG-5 deferred).
- No vendor / model / provider / engine selector in Block D ("which model to use").
- No removal of the Phase B Variation Panel.
- No mutation of any closure event (append-only).

---

## 7. PR-4 — Delivery Center A–F + Publish Feedback

### 7.1 Operator-visible outcome

The Matrix Script branch of `gateway/app/templates/task_publish_hub.html` is re-organised around the publishable-output surface defined by [matrix_script_delivery_center_wireframe_v1.md](matrix_script_delivery_center_wireframe_v1.md):

- **Block A — Main `final_video` slot**: recommended-candidate ⭐ marker, provenance pill (current/historical via Recovery PR-1 inferred label), primary media slot (server-rendered placeholder + final-media handle when present; tracked-gap operator-language line when absent), per-variant tabs.
- **Block B — Required deliverables**: 7-row deliverable table (`variation_manifest` / `slot_bundle` / `subtitle_bundle` / `audio_preview` / `copy_bundle` / `metadata` / `manifest`) with `required` + `blocking_publish` columns from Plan C amendment.
- **Block C — Optional `scene_pack` (non-blocking)**: `SCENE_PACK_BLOCKING_ALLOWED = False` enforced; never blocks publish-readiness.
- **Block D — Copy bundle**: 标题 / Hashtags / CTA / 评论关键词 from `delivery_copy_bundle_view`.
- **Block E — Publish status / Publish Feedback**: per-variant row table + append-only event log + "+ 记录发布事件" action (POSTs to existing closure endpoint with `event_kind == "operator_publish"`).
- **Block F — Iteration / Archive**: operator-language iteration recommendation lines from `publish_backfill_readiness_view` + "归档此任务" button.

The header carries the publish-readiness banner consuming `compute_publish_readiness` directly (RC-A7).

### 7.2 Backend / runtime feeds consumed

| Block | Service / endpoint | File |
|---|---|---|
| Header — Stage / result pill | `derive_matrix_script_eight_stage_state` + `derive_matrix_script_task_area_result_status` | gateway/app/services/matrix_script/task_area_convergence.py + result_status_view.py |
| Header — Publish gate banner + next-action | `compute_publish_readiness` (head_reason → operator label) | publish_readiness producer (Recovery PR-1 substrate) |
| A — Recommended-candidate marker / provenance | `derive_matrix_script_delivery_comprehension.final_video_primary` + L3 `final_provenance` (Recovery PR-1 inferred label) | gateway/app/services/matrix_script/delivery_comprehension.py |
| A — Final-media handle | `result_packet_binding.artifact_lookup` for `final_video` row (E.MS.1 substrate) | gateway/app/services/matrix_script/delivery_comprehension.py + Plan E PR-1 substrate |
| A — Variant tabs | `derive_matrix_script_preview_compare_view` per-variant rows | gateway/app/services/matrix_script/preview_compare_view.py |
| B — Required deliverable rows + zoning | `derive_matrix_script_delivery_comprehension` + `factory_delivery_contract_v1` Plan C `required` / `blocking_publish` | delivery_comprehension.py + factory_delivery_contract_v1.md |
| B — Per-row status | `derive_matrix_script_delivery_ready_package` | delivery_ready_package_view.py |
| C — `scene_pack` non-blocking | `SCENE_PACK_BLOCKING_ALLOWED = False` | matrix_script/delivery_binding.py |
| D — Copy bundle fields | `derive_matrix_script_delivery_copy_bundle` | delivery_copy_bundle_view.py |
| E — Per-variant row table | Phase D.0 closure `variation_feedback[]` (read via `get_closure_view_for_task`) | publish_feedback_closure.py + closure_binding.py |
| E — Event log | `feedback_closure_records[]` (append-only) | publish_feedback_closure.py |
| E — Record-publish form | `POST /api/matrix-script/closures/{task_id}/events` with closed `D1_EVENT_KINDS` | gateway/app/routers/matrix_script_closure.py |
| E — Closed enums consumed | `D1_PUBLISH_STATUS_VALUES`, `D1_EVENT_KINDS`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES`, `CHANNEL_METRICS_KEYS`, `ACTOR_KINDS` | publish_feedback_closure.py |
| F — Iteration recommendation | `derive_matrix_script_publish_backfill_readiness` | publish_backfill_readiness_view.py |
| F — Archive event | closure event `record_kind == "archive_action"` | publish_feedback_closure.py |

All feeds already exist. PR-4 introduces no new helper module and no new endpoint.

### 7.3 Secondary diagnostics only (preserved verbatim)

- Existing Phase D.0 closure inspector view (engineering-facing) preserved verbatim.
- Existing per-variant metrics raw-payload inspector (when present) preserved verbatim.
- Existing OWC-MS PR-3 server-rendered backfill bundle (zero-lane empty-state messaging) preserved verbatim — this PR organises around it; it does not replace it.

### 7.4 Acceptance evidence

| ID | Evidence |
|---|---|
| RO-4.1 | `task_publish_hub.html` Matrix Script branch renders Blocks A–F in document order per [delivery wireframe §3 / §4 / §5 / §6 / §7 / §8 / §9](matrix_script_delivery_center_wireframe_v1.md). |
| RO-4.2 | Block A primary slot renders recommended-candidate ⭐ marker, provenance pill, final-media handle (or tracked-gap), variant tabs; **no fabricated `final_video` URL under any input** (RC-R8 audit). |
| RO-4.3 | Block B 7-row required-deliverable table renders with `required` + `blocking_publish` columns sourced from Plan C amendment per `factory_delivery_contract_v1`; per-row status from `derive_matrix_script_delivery_ready_package`. |
| RO-4.4 | Block C `scene_pack` always non-blocking; even under adversarial `pack.required = True` payload input, the row renders with `SCENE_PACK_BLOCKING_ALLOWED = False` enforcement and does not block publish-readiness. |
| RO-4.5 | Block D copy bundle renders 标题 / Hashtags / CTA / 评论关键词 from `derive_matrix_script_delivery_copy_bundle`; no free-text editing affordance. |
| RO-4.6 | Block E "+ 记录发布事件" form posts to `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_publish"` ONLY; no enum widening; no new endpoint; closure log is append-only (no mutation / deletion). |
| RO-4.7 | Block E publish-status column reads only from `D1_PUBLISH_STATUS_VALUES`; no second-source publish-state derivation. |
| RO-4.8 | Block F iteration recommendation reads from `derive_matrix_script_publish_backfill_readiness.next_iteration_text` (operator language); archive button posts an `operator_publish` event followed by a `record_kind == "archive_action"` event per existing semantics. |
| RO-4.9 | Header publish-gate banner consumes `compute_publish_readiness` directly; no second-source `publishable` derivation (RC-A7); zero re-implementation of lane derivation across blocks. |
| RO-4.10 | Hot Follow + Digital Anchor publish-hub branches bytewise unchanged. |
| RO-4.11 | Test floor: ≥ 50 dedicated test cases across PR-4 service / template / closure-event suites. |
| RO-4.12 | Adjacent regression: closure-D.1 endpoint test suite PASS; cross-line preservation tests PASS; OWC-MS PR-3 zero-lane empty-state messaging preserved. |
| RO-4.13 | No new endpoint, no contract / schema / packet / validator change, no new closed-enum widening. |

### 7.5 Hard non-goals

- No metric-grounded iteration recommendation (BG-5 deferred to a future post-Plan-E analytics wave).
- No `metrics_snapshot.raw_payload_ref` resolver (BG-4 deferred).
- No first-class L3 `final_provenance` field emission (BG-2 — Recovery PR-1 inferred label is the binding render basis for this PR; first-class field emission is gated to a future Plan E phase).
- No artifact_lookup expansion to non-`final_video` rows (BG-3 deferred — variant tabs render tracked-gap thumbnails for non-`final_video` previews).
- No inline `final_video` player (IG-5 deferred — operators continue to jump to R2/CDN URL).
- No "duplicate as new task" affordance from Block F (IG-3 deferred).
- No vendor / model / provider / engine column or label.
- No mutation / deletion of any closure event (append-only).
- No removal of the existing Phase D.0 closure inspector view.

---

## 8. Closeout — aggregating audit + signoff

### 8.1 Closeout document

A new docs-only closeout file at `docs/execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_ORIENTED_UI_CLOSEOUT_v1.md` aggregates audit across PR-1..PR-4 + signoff. It mirrors the structure of [docs/execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md).

### 8.2 Acceptance rows

| ID | Acceptance |
|---|---|
| RO-A1 | PR-1 (Task Area card refit) MERGED; RO-1.1..RO-1.7 PASS with explicit evidence pointers. |
| RO-A2 | PR-2 (Workbench Blocks A / B / C) MERGED; RO-2.1..RO-2.9 PASS with explicit evidence pointers. |
| RO-A3 | PR-3 (Workbench Blocks D / E / F) MERGED; RO-3.1..RO-3.10 PASS with explicit evidence pointers. |
| RO-A4 | PR-4 (Delivery Center A–F + Publish Feedback) MERGED; RO-4.1..RO-4.13 PASS with explicit evidence pointers. |
| RO-A5 | Operator-comprehension demonstration recorded per PR §6 walkthrough block (one operator session per surface — Task Area, Workbench, Delivery Center; six 10-second questions answered per surface). |
| RO-A6 | No-fake-`final_video` audit clean across PR-1..PR-4 (RC-R8 invariant carries forward). |
| RO-A7 | Single-source `publish_readiness` audit clean — no helper imports or re-implements `compute_publish_readiness` derivation (RC-A7 invariant carries forward). |
| RO-A8 | No vendor / model / provider / engine UI surfaced anywhere across PR-1..PR-4. |
| RO-A9 | Digital Anchor preservation: zero `gateway/app/services/digital_anchor/` / `docs/contracts/digital_anchor/` / digital_anchor template paths in any PR change set (recovery amendment §7 + post-OWC addendum §2.3). |
| RO-A10 | Hot Follow preservation: zero `gateway/app/services/hot_follow*` / `docs/contracts/hot_follow*` / hot_follow template paths in any PR change set; coordinator confirms Hot Follow golden-path live regression PASS. |
| RO-A11 | Forbidden-scope full-pass aggregating across PR-1..PR-4: no new contract / no closed-enum widening / no new structural service module / no operator-driven Phase B authoring / no Asset Supply file touch / no donor namespace import / no React/Vite rebuild / no durable persistence / no PR slice bundling. |
| RO-A12 | Product-flow module-presence audit (per ENGINEERING_RULES.md §13): each PR's claimed scope is operator-visible on the relevant `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Matrix Script branch; reviewer walkthrough recorded. |
| RO-A13 | Four-party signoff — Architect (Raobin) + Reviewer (Alisa) + Operations Coordinator (Jackie) + Product Manager — at §10 / §11 of the closeout document. |

### 8.3 Signoff block (template)

The closeout document's §10 / §11 carries the four-party signoff lines as `<fill>` placeholders that bind on the docs-only follow-on RO-A13 signoff PR (precedent: Recovery Wave Closeout #153 + RC-A13 signoff #154).

### 8.4 What this closeout unlocks

This closeout's RO-A13 signoff PR merge unlocks ONLY what is explicitly stated. It does NOT advance:

- Plan A live-trial Matrix Script execution closeout (which is already a separate sequence step per alignment map §7).
- Platform Runtime Assembly Wave (independently gated).
- Capability Expansion Gate Wave (independently gated).
- Plan E A7 / UA7 / RA7 closeout signoffs (independently pending in Raobin / Alisa / Jackie / PM queue).
- OWC-MS MS-A7 / OWC-DA DA-A7 closeout signoffs (independently pending).

Whatever this closeout does unlock — typically the next docs-only step in whatever sequence the alignment map carries at that time — MUST be authored in §11 of the closeout document at authoring time, not pre-decided here.

---

## 9. Cross-PR discipline (binding for PR-1..PR-4 + Closeout)

| Discipline | Rule | Authority |
|---|---|---|
| Strict ordering | PR-1 must merge before PR-2 opens; PR-2 before PR-3; PR-3 before PR-4; PR-4 before Closeout authoring | OWC-MS / OWC-DA / Recovery Wave precedent |
| Byte isolation per PR | each PR's `git diff --stat` shows zero touch in non-scope paths (Hot Follow / Digital Anchor / Asset Supply / unrelated Matrix Script files) | recovery amendment §7 + recovery gate spec §4 |
| Single source of truth for `publishable` | every PR's blocks consuming `publishable` consume `compute_publish_readiness` directly | RC-A7 |
| No fake `final_video` | every PR audited for synthesised `final_video` / `publish_url` echo even under adversarial input | RC-R8 |
| Append-only closure | every closure-D.1 affordance posts events; never mutates / deletes | publish_feedback_closure_contract_v1 |
| No closed-enum widening | no PR widens `STAGE_*`, `STATUS_*`, `RECOMMENDED_BUCKET_*`, `READINESS_*`, `D1_EVENT_KINDS`, `D1_PUBLISH_STATUS_VALUES`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES`, `head_reason` | recovery gate spec §4 + factory_packet_envelope_contract_v1 E5 |
| No new contract | no PR authors a contract or amends an existing one | recovery amendment §7 |
| No new structural service module | each PR is pure presentation-layer (template + thin presenter wiring); no new helper module created | recovery gate spec §4 |
| Test floor per PR | RO-1.4 / RO-2.7 / RO-3.8 / RO-4.11 | mirrors recovery / OWC test-floor precedent |
| Cross-line byte stability test | each PR includes a test asserting the cross-line invariant (Hot Follow card / panel / publish branches bytewise unchanged) | precedent from `test_matrix_script_closure_review_zone_values_unchanged_by_da_addition` |
| Product-flow module-presence | each PR extends the relevant template branch; no service-only / projection-only / contract-only PR may claim operator-ready in this wave | ENGINEERING_RULES.md §13 |
| Reading-declaration template | every PR cites: this slicing addendum + the relevant wireframe + the master plan + recovery amendment §7 + recovery gate spec §4 + the wave's gate spec authored under §2 (4) | recovery wave precedent |
| Coordinator confirmation block | PR-1..PR-4 each carry a `<fill>` coordinator-confirmation-of-Hot-Follow-golden-path block that the Closeout's RO-A10 row aggregates | Recovery Wave / OWC precedent |

---

## 10. Reading declaration

This addendum consumes the same reading set as [matrix_script_result_oriented_ui_plan_v1.md §14](matrix_script_result_oriented_ui_plan_v1.md). Additional precedents specifically consulted for slicing shape:

- [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md) §5 (PR slicing / module-to-PR allocation).
- [docs/reviews/owc_da_gate_spec_v1.md](../reviews/owc_da_gate_spec_v1.md) §5.
- [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) §5 / §6 / §10.
- [docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md).
- [docs/execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md).
- [docs/execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md).
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §13 Product-Flow Module Presence.

Documentation only — no code, no UI implementation, no contract authoring, no schema mutation, no template change, no test change, no runtime change.
