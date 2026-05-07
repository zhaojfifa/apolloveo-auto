# Matrix Script Result-Oriented UI Plan v1

Date: 2026-05-07
Status: **Design package only.** No code, no UI implementation, no contract authoring, no schema mutation, no template change, no test change, no runtime change. This document declares the operator-visible target shape of Matrix Script as a result-oriented video production line. Authoring this document does NOT open any implementation gate.
Authority of creation:
- Product authority: [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md) §§4 / 5 / 6 / 7 / 11.
- Recovery authority: [docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md](../product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md) §§5 / 7 (hard boundaries).
- Recovery gate spec: [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) RC-R1..RC-R8 + §4 forbidden scope.
- Recovery closeout: [docs/execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md) §10 SIGNED 2026-05-07.
- Surface authority: [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](ApolloVeo_Operator_Visible_Surfaces_v1.md), [docs/design/surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md), [docs/design/surface_workbench_lowfi_v1.md](surface_workbench_lowfi_v1.md), [docs/design/surface_delivery_center_lowfi_v1.md](surface_delivery_center_lowfi_v1.md).
- Bootloader: [CLAUDE.md](../../CLAUDE.md), [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md).
- Alignment map: [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).

This file does **not** redefine product authority, contract authority, or wave authority. When this document conflicts with any of the above, the underlying authority wins.

---

## 1. What this document is and is not

### 1.1 Is

- A frontend-design-first declaration of how Matrix Script should look to an operator who has been told "produce a publishable video result", not to a reviewer reading packet internals.
- A binding mapping from each operator-visible UI block back to an existing Matrix Script presentation service, line contract, or cross-line contract object — i.e. **every block on every wireframe must point at a backend object that already exists or be marked as a gap**.
- A list of explicit gaps (backend gap / presenter gap / interaction gap) that future implementation PRs may close, **without solving them in this step**.
- The page-level information architecture (IA), the operator journey, the state vocabulary shown to operators, and the explicit distinction between Task Area, Workbench, Delivery Center, and Publish Feedback as four operator-visible work zones for this line.

### 1.2 Is not

- Not a contract. It does not author or mutate any line contract or factory contract.
- Not a packet truth source. It does not invent state outside artifact facts / current attempt / publish readiness.
- Not a runtime spec. It does not specify endpoints, queues, workers, vendor routing, or storage layout.
- Not a vendor / model / provider / engine catalog. Operator-visible payloads MUST NOT carry `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any donor namespace identifier.
- Not a Digital Anchor doc. Digital Anchor scope is explicitly out of scope (recovery amendment §7 + post-OWC addendum §2.3).
- Not a Hot Follow doc. Hot Follow files are not touched. Hot Follow is consulted as a UX benchmark only.
- Not a wave authority. It does not open the next engineering wave; the alignment map's frozen next engineering sequence remains in force.

---

## 2. Design rationale (why this shape)

The Matrix Script line has, until the Recovery Wave closeout, presented operators with a contract-heavy inspection page: axes / cells / slots tables, refs counters, gate badges, validator reports. That posture is faithful to the packet envelope but is not faithful to what the line is for. The product authority [docs/product/matrix_script_product_flow_v1.md §11](../product/matrix_script_product_flow_v1.md) defines the line as **"面向矩阵运营与快速试错的脚本驱动成片产线"** whose success criterion is whether it produces *publishable multi-variant final video*, not whether it surfaces packet internals.

The Recovery Wave (RC PR-1..PR-4 + closeout PR #153 + signoff PR #154) landed the **server-side projections** that turn packet truth into operator-language summaries: result status, recommended action, readable script, variant candidates, delivery-ready package, publish/backfill readiness. The presentation services exist. What is now needed is a **deliberate IA on top of those services** that organises the operator's work into a result-oriented flow, with a single primary deliverable (`final_video`) and clearly demarcated supporting deliverables.

The six-question test is the discipline. An operator landing on a Matrix Script task — at the Task Area, the Workbench, or the Delivery Center — must be able to answer all six within 10 seconds without opening any inspector, validator drawer, or contract document:

1. What is this task trying to produce?
2. Which variants are worth generating or reviewing?
3. What is blocked right now?
4. What should I do next?
5. Which candidate is currently recommended?
6. Is there a publishable video result yet?

Every wireframe in this design package is structured so that the answers to those six questions live above the fold of the surface they belong to.

---

## 3. Operator journey (end-to-end)

The journey below is the canonical happy path. Every step names the surface the operator is on, the operator-language signal they read, the action they take, and the closed-state sentinel that gates the next step. No step exposes vendor / model / provider / engine controls.

| # | Surface | Operator reads | Operator does | Closed state that advances |
|---|---|---|---|---|
| 1 | Task Area · New Task | Line-specific intake (subject, audience, target language) | Posts a Matrix Script intake → packet | Phase A entry payload accepted (existing route `/tasks/matrix-script/new`) |
| 2 | Task Area · Card | Eight-stage badge `已创建` | Opens task → routes by best-next-action | `STAGE_CREATED → STAGE_PENDING_CONFIG` |
| 3 | Workbench · Block A 脚本结构 | Hook / Body / CTA (operator language) | Reads structure; if ready, launches **Generate** | structure resolved (no operator authoring of `axes[]` / `cells[]` / `slots[]` in this wave) |
| 4 | Workbench · Block C 变体策略 | Variant count, per-variant differentiator | Confirms variants; launches generation | `STAGE_PENDING_CONFIG → STAGE_GENERATING` |
| 5 | Workbench · Block D 生成动作 | Preconditions block; recommended action | Clicks "Generate" / "Regenerate blocked" | `STAGE_GENERATING → STAGE_AWAITING_REVIEW` |
| 6 | Workbench · Block E 候选评审 | Per-variant card: preview slot, subtitle / audio / package status, recommended marker | Picks a candidate / requests regen | `STAGE_AWAITING_REVIEW → STAGE_FINAL_READY` |
| 7 | Delivery Center | `final_video` primary; supporting deliverables; publish readiness | Confirms publishable | `STAGE_FINAL_READY → STAGE_PUBLISHABLE` |
| 8 | Delivery Center · Publish Feedback | Channel / account / time / url / status / metrics-stub | Logs publish event | `STAGE_PUBLISHABLE → STAGE_BACKFILLED` |
| 9 | Task Area · Card | "已归档" + iteration hint | Archives / launches next iteration | `STAGE_BACKFILLED → STAGE_ARCHIVED` |

The eight-stage closed enum referenced above is the existing closed state in [`gateway/app/services/matrix_script/task_area_convergence.py`](../../gateway/app/services/matrix_script/task_area_convergence.py): `STAGE_CREATED`, `STAGE_PENDING_CONFIG`, `STAGE_GENERATING`, `STAGE_AWAITING_REVIEW`, `STAGE_FINAL_READY`, `STAGE_PUBLISHABLE`, `STAGE_BACKFILLED`, `STAGE_ARCHIVED`. This document neither widens nor renames it.

---

## 4. Page-level information architecture (IA)

Matrix Script is one production line. The operator interacts with the line across **four work zones**, with an explicit single-direction flow between them. Each zone has a single primary purpose and a single primary backend feed.

### 4.1 Four zones (binding distinction)

| Zone | Primary purpose | Primary feed | Wireframe |
|---|---|---|---|
| **A. Task Area** | Production management — what tasks exist, which are blocked, where to go | `derive_matrix_script_eight_stage_state` + `derive_matrix_script_task_card_summary` + `derive_matrix_script_task_area_result_status` | [matrix_script_task_area_wireframe_v1.md](matrix_script_task_area_wireframe_v1.md) |
| **B. Workbench** | Result-oriented production workbench — script, variants, generation, candidate review | `derive_matrix_script_workbench_comprehension` + `derive_matrix_script_script_structure_view` + `derive_matrix_script_readable_variants` + `derive_matrix_script_preview_compare_view` + `derive_matrix_script_review_zone_view` + `derive_matrix_script_recommended_action` + `derive_matrix_script_workbench_result_summary` | [matrix_script_workbench_wireframe_v1.md](matrix_script_workbench_wireframe_v1.md) |
| **C. Delivery Center** | Publishable output center — `final_video` primary, supporting deliverables, publish readiness | `derive_matrix_script_delivery_comprehension` + `derive_matrix_script_delivery_ready_package` + `derive_matrix_script_delivery_copy_bundle` + `derive_matrix_script_publish_backfill_readiness` + `compute_publish_readiness` | [matrix_script_delivery_center_wireframe_v1.md](matrix_script_delivery_center_wireframe_v1.md) |
| **D. Publish Feedback** | Per-variant publish event log + metrics backfill + iteration hint | `derive_matrix_script_delivery_backfill` + Phase D.0 closure (`get_closure_view_for_task` / `apply_event_for_task`) | embedded in Delivery Center wireframe §"Publish Feedback" + Task Area card "open publish feedback" jump |

Publish Feedback is a sub-zone of Delivery Center on the surface (single page) but it is named separately because its operator semantics are different (post-publish observation vs pre-publish packaging). Neither implementation nor IA may merge them silently — Publish Feedback always renders with its own header and timestamp lane.

### 4.2 Single-direction flow

```
Task Area
    │
    │  open workbench
    ▼
Workbench  ──────► Delivery Center  ──────► Publish Feedback
    ▲                  │                        │
    │                  │  back-link             │  iteration hint
    └──────────────────┴────────────────────────┘
```

Operators may always step **back** to the Task Area from any zone. Operators may always step **forward** along the flow when the closed state allows. There is no zone that allows authoring of packet truth — all authoring is constrained to the Workbench's `ready_state ∈ {ready}` Generate / Regenerate block plus Delivery Center's publish event posting.

### 4.3 What each zone must NOT show

| Zone | Forbidden surfaces |
|---|---|
| Task Area | vendor / model / provider / engine; raw `cell_id` / `slot_id` / `content://` handles; per-variant inspector; validator report; donor / supply UI |
| Workbench | vendor / model / provider / engine; raw `axes[]` / `cells[]` authoring (Phase B authoring is system-only this wave per gate spec §4.3); donor / supply UI; `not_implemented_phase_c` placeholder wording (retired by Plan E PR-1) |
| Delivery Center | vendor / model / provider / engine; vendor name in `final_video` slot; fake `final_video` / fabricated `publish_url` (RC-R8 audit); validator report drawer (kept off this surface — gate badge only) |
| Publish Feedback | vendor / model / provider / engine; second-source publish state (must consume only `D1_PUBLISH_STATUS_VALUES` enum) |

---

## 5. State model shown to operators

Operator-visible state on Matrix Script is the union of three closed sources, all already produced by existing services. **No new state is invented.**

| State family | Source | Closed values shown to operators |
|---|---|---|
| Task lifecycle stage | `derive_matrix_script_eight_stage_state` (matrix_script/task_area_convergence.py) | `已创建` / `待配置` / `生成中` / `待校对` / `成片完成` / `可发布` / `已回填` / `已归档` |
| Result status (Task Area card + Workbench summary) | `derive_matrix_script_task_area_result_status` + `derive_matrix_script_workbench_result_summary` (matrix_script/result_status_view.py) | `STATUS_READY` (do X next) / `STATUS_BLOCKED` (missing Y) / `STATUS_COMPLETED` (publishable result exists) |
| Recommendation bucket (per-variant + per-task next-action lane) | `derive_matrix_script_preview_compare_view` + `derive_matrix_script_recommended_action` (matrix_script/preview_compare_view.py + recommended_action_view.py) | `RECOMMENDED_BUCKET_PUBLISHABLE` / `RECOMMENDED_BUCKET_BLOCKED` / `RECOMMENDED_BUCKET_UNDETERMINED` |
| Publish readiness (Delivery Center + Publish Feedback) | `compute_publish_readiness` (publish_readiness producer; Recovery PR-1) → `head_reason ∈ {publishable_ok, ready_gate_blocking, publish_not_ready, compose_not_ready, final_missing, final_stale, final_provenance_historical, required_deliverable_missing, required_deliverable_blocking, unresolved}` | rendered as operator-language head-reason labels (`HEAD_REASON_LABELS_ZH`) — never as raw enum |
| Delivery lane | `derive_matrix_script_delivery_comprehension` (matrix_script/delivery_comprehension.py) | `required_blocking` / `required_non_blocking` / `optional_non_blocking` |
| Per-deliverable readiness (Delivery Ready Package) | `derive_matrix_script_delivery_ready_package` (matrix_script/delivery_ready_package_view.py) | `READINESS_PUBLISHABLE_NOW` / `READINESS_GATED` / `READINESS_ALREADY_PUBLISHED` / `READINESS_ALREADY_FAILED` / `READINESS_TRACKED_GAP` |
| Closure event kind (Publish Feedback) | `D1_EVENT_KINDS` (matrix_script/publish_feedback_closure.py) | `operator_publish` / `operator_retract` / `operator_note` / `platform_callback` / `metrics_snapshot` |
| Closure publish status (Publish Feedback) | `D1_PUBLISH_STATUS_VALUES` | `pending` / `published` / `failed` / `retracted` |
| Review zone (Workbench Block E review) | `REVIEW_ZONE_VALUES` (closure-D.1 additive enum) | `subtitle` / `dub` / `copy` / `cta` |

Operators never see L1 (`step_status`), L4 (`ready_state`) raw enum, validator report references, or any field forbidden by [`factory_packet_envelope_contract_v1`](../contracts/factory_packet_envelope_contract_v1.md) E5 / [`factory_packet_validator_rules_v1`](../contracts/factory_packet_validator_rules_v1.md) R5.

---

## 6. Section-by-section field mapping (master index)

Every operator-visible block in the four wireframes maps to one row below. Wireframe documents repeat the relevant slice of this table inline; this section is the master index.

### 6.1 Task Area card → backend

| Card region | Backend feed | Service file | Closed enum |
|---|---|---|---|
| Subject / goal headline | `task["config"]["entry"].subject` (sanitised) | task_card_summary.py | — |
| Line marker `matrix_script` | `kind` constant | template gate `kind == "matrix_script"` | — |
| Variant count | `derive_matrix_script_task_card_summary().variant_count` | task_card_summary.py | — |
| Publishable variant count | `derive_matrix_script_task_card_summary().publishable_count` | task_card_summary.py | — |
| Best candidate marker | `derive_matrix_script_task_card_summary().best_version` | task_card_summary.py | `RECOMMENDED_BUCKET_PUBLISHABLE` (gate) |
| Current blocker | `derive_matrix_script_task_card_summary().blocker` (operator-language) | task_card_summary.py | (free-form label; sourced from blockers/head_reason) |
| Latest generation time | `derive_matrix_script_task_card_summary().last_generated_at` | task_card_summary.py | — |
| Eight-stage badge | `derive_matrix_script_eight_stage_state` | task_area_convergence.py | `STAGE_*` |
| Three-tier lane (script/variant/publish) | `derive_matrix_script_three_tier_lanes` | task_area_convergence.py | per-lane closed sentinels |
| Result status pill | `derive_matrix_script_task_area_result_status` | result_status_view.py | `STATUS_READY` / `STATUS_BLOCKED` / `STATUS_COMPLETED` |
| Next action chip | `derive_matrix_script_task_area_result_status.next_action_label` | result_status_view.py | (operator-language sentence) |
| Jump: open workbench | router `/tasks/{id}` (existing) | gateway/app/routers/tasks.py | — |
| Jump: open delivery | router `/tasks/{id}/publish-hub` (existing) | gateway/app/routers/tasks.py | — |
| Jump: open publish feedback | same publish-hub anchor `#publish-feedback` | template anchor | — |

### 6.2 Workbench → backend

| Block | Backend feed | Service file | Closed enum |
|---|---|---|---|
| A. Task Header / Goal Summary | `derive_matrix_script_workbench_comprehension` (header / 任务身份 / 下一步) + `derive_matrix_script_workbench_result_summary` | workbench_comprehension.py + result_status_view.py | `STATUS_*` |
| B. Script Structure (Hook / Body / CTA / keywords / forbidden terms) | `derive_matrix_script_script_structure_view` | script_structure_view.py | — |
| C. Variant Strategy (per-variant differentiator) | `derive_matrix_script_readable_variants` (operator-readable) + `derive_matrix_script_workbench_comprehension.variant_summary` | readable_variant_view.py + workbench_comprehension.py | — |
| D. Generate / Regenerate Action | `derive_matrix_script_recommended_action` + `compute_publish_readiness.head_reason` (for blocked-reason operator label) | recommended_action_view.py + publish_readiness producer | `RECOMMENDED_BUCKET_*` + head-reason label |
| E. Result Review (per-variant card) | `derive_matrix_script_preview_compare_view` + `derive_matrix_script_review_zone_view` + `derive_matrix_script_qc_diagnostics_view` + `derive_matrix_script_delivery_ready_package` | preview_compare_view.py + review_zone_view.py + qc_diagnostics_view.py + delivery_ready_package_view.py | `RECOMMENDED_BUCKET_*` + `REVIEW_ZONE_VALUES` + `READINESS_*` |
| F. Delivery Block (link out + readiness teaser) | `derive_matrix_script_delivery_comprehension` (lane summary) + `compute_publish_readiness.publishable` (gate teaser) | delivery_comprehension.py + publish_readiness producer | lane closed-set + `publishable: bool` |

### 6.3 Delivery Center → backend

| Block | Backend feed | Service file | Closed enum |
|---|---|---|---|
| `final_video` primary slot | `derive_matrix_script_delivery_comprehension.final_video_primary` (server-rendered placeholder) + L3 `final_provenance` (Recovery PR-1 emitter) | delivery_comprehension.py + L3 emitter | provenance ∈ {`current`, `historical`} |
| Required deliverables lane (`required_blocking` + `required_non_blocking`) | `derive_matrix_script_delivery_comprehension` lanes | delivery_comprehension.py | lane closed-set |
| Optional scene_pack lane (non-blocking) | `derive_matrix_script_delivery_comprehension.optional_non_blocking` | delivery_comprehension.py | `SCENE_PACK_BLOCKING_ALLOWED = False` constant |
| Copy bundle | `derive_matrix_script_delivery_copy_bundle` | delivery_copy_bundle_view.py | — |
| Publish readiness banner | `compute_publish_readiness` | publish_readiness producer | `head_reason` enum → operator-language label |
| Publish feedback entry | Phase D.0 closure: `get_closure_view_for_task` + `POST /api/matrix-script/closures/{task_id}/events` | publish_feedback_closure.py + matrix_script_closure router | `D1_EVENT_KINDS` + `D1_PUBLISH_STATUS_VALUES` |
| Iteration hint | `derive_matrix_script_publish_backfill_readiness` (gap taxonomy → next-iteration text) | publish_backfill_readiness_view.py | `READINESS_*` |
| Archive | Phase D.0 closure `feedback_closure_records[].record_kind == "archive_action"` | publish_feedback_closure.py | `RECORD_KINDS` |

### 6.4 Publish Feedback → backend

| Row field | Backend feed | Service file | Closed enum |
|---|---|---|---|
| Channel | `variation_feedback[].channel` | publish_feedback_closure.py | — |
| Account | `variation_feedback[].account` | publish_feedback_closure.py | (rendered as tracked-gap when absent) |
| Publish time | `variation_feedback[].publish_time` (or fallback ordering: D.1 publish-state-mutating record → row.last_event_recorded_at → metrics captured_at) | publish_feedback_closure.py | — |
| Publish URL | `variation_feedback[].publish_url` (rendered only when present; never echoed if absent — RC-R8) | publish_feedback_closure.py | — |
| Publish status | `variation_feedback[].publish_status` | publish_feedback_closure.py | `D1_PUBLISH_STATUS_VALUES` |
| Metrics snapshot | `channel_metrics` (`channel_id`, `captured_at`, optional `impressions` / `views` / `engagement_rate` / `completion_rate` / `raw_payload_ref`) | publish_feedback_closure.py | `CHANNEL_METRICS_KEYS` |
| Event log | `feedback_closure_records[]` append-only | publish_feedback_closure.py | `D1_EVENT_KINDS`, `RECORD_KINDS` |

---

## 7. Allowed and forbidden actions (operator-visible)

### 7.1 Allowed actions (operator-eligible)

| Surface | Action | Backend hook | Closed precondition |
|---|---|---|---|
| Task Area | Open workbench | route `/tasks/{id}` | task exists |
| Task Area | Open delivery | route `/tasks/{id}/publish-hub` | `kind == "matrix_script"` |
| Task Area | Open publish feedback | publish-hub anchor | same |
| Workbench | Generate (initial) | existing post action wired into `capability_plan.kind == "variation"` execution | `STAGE_PENDING_CONFIG` + `evidence.ready_state ∈ {ready}` |
| Workbench | Regenerate blocked variant | same execution path scoped per `cell_id` | `RECOMMENDED_BUCKET_BLOCKED` for that variant |
| Workbench | Pick recommended candidate | per-variation operator decision recorded as `operator_note` D.1 event scoped by `review_zone` | `STAGE_AWAITING_REVIEW` |
| Workbench | Submit zone-scoped review (subtitle / dub / copy / cta) | `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_note"` + `review_zone ∈ REVIEW_ZONE_VALUES` | same |
| Delivery Center | Confirm publishable | render-only (gates Publish Feedback CTA) | `compute_publish_readiness.publishable == True` |
| Publish Feedback | Log publish event | `POST /api/matrix-script/closures/{task_id}/events` with `event_kind == "operator_publish"` | `STAGE_PUBLISHABLE` |
| Publish Feedback | Log retract / metrics-snapshot / note | same endpoint with appropriate `event_kind` | per closure D.1 contract |
| Task Area / Delivery Center | Archive | closure event `event_kind == "operator_publish"` followed by `record_kind == "archive_action"` (existing semantics) | `STAGE_BACKFILLED` |

### 7.2 Forbidden actions (operator-visible)

These are forbidden in the design AND forbidden by upstream contract / wave gate. Surfacing any of them is a design failure.

- Choosing vendor / model / provider / engine — forbidden by [factory_packet_envelope_contract_v1](../contracts/factory_packet_envelope_contract_v1.md) E5 + validator R3.
- Authoring `axes[]` / `cells[]` / `slots[]` (Phase B operator authoring) — forbidden by Plan E gate spec §4.3 (operator-driven Phase B authoring deferred); recovery wave preserved this freeze.
- Surfacing raw `content://` handles, `cell_id`, `slot_id`, `binds_cell_id`, `script_slot_ref`, packet-debug wording, ref counters — all forbidden in operator-visible surfaces by [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](ApolloVeo_Operator_Visible_Surfaces_v1.md) §"Operator-visible payload sanitization".
- Authoring or echoing fake `final_video` / fabricated `publish_url` — forbidden by recovery gate spec RC-R8.
- Re-deriving `publishable` outside `compute_publish_readiness` — forbidden by recovery gate spec RC-A7 (no second truth source).
- Operating on Digital Anchor surfaces from Matrix Script flows — forbidden by recovery amendment §7 + post-OWC addendum §2.3.
- Touching Hot Follow files — forbidden by recovery amendment §7.
- Asset Supply / B-roll page or promote intent — gated to Plan E; not surfaced from Matrix Script.

---

## 8. Mapping from existing contract / runtime surfaces into UI blocks (consolidated)

This section is the consolidated authority pointer table for every UI block. Wireframes cite this table by row reference (e.g. "Task Area Card 卡片身份 → §8 row 1").

| # | UI block | Authority object (contract or service) | Authority path |
|---|---|---|---|
| 1 | Task Area card identity | `factory_packet_envelope_contract_v1` `line_id` const | [docs/contracts/factory_packet_envelope_contract_v1.md](../contracts/factory_packet_envelope_contract_v1.md) |
| 2 | Task Area card eight-stage badge | `derive_matrix_script_eight_stage_state` | gateway/app/services/matrix_script/task_area_convergence.py |
| 3 | Task Area card 8-field summary | `derive_matrix_script_task_card_summary` | gateway/app/services/matrix_script/task_card_summary.py |
| 4 | Task Area card result status | `derive_matrix_script_task_area_result_status` | gateway/app/services/matrix_script/result_status_view.py |
| 5 | Workbench A header / goal | `derive_matrix_script_workbench_comprehension` (`header`, `task_identity`) | gateway/app/services/matrix_script/workbench_comprehension.py |
| 6 | Workbench A result summary | `derive_matrix_script_workbench_result_summary` | gateway/app/services/matrix_script/result_status_view.py |
| 7 | Workbench B script structure | `derive_matrix_script_script_structure_view` | gateway/app/services/matrix_script/script_structure_view.py |
| 8 | Workbench C variant strategy (operator-readable) | `derive_matrix_script_readable_variants` | gateway/app/services/matrix_script/readable_variant_view.py |
| 9 | Workbench D recommended action / blocked reason | `derive_matrix_script_recommended_action` + `compute_publish_readiness.head_reason` | gateway/app/services/matrix_script/recommended_action_view.py + publish_readiness producer |
| 10 | Workbench E preview compare | `derive_matrix_script_preview_compare_view` | gateway/app/services/matrix_script/preview_compare_view.py |
| 11 | Workbench E review zones | `derive_matrix_script_review_zone_view` | gateway/app/services/matrix_script/review_zone_view.py |
| 12 | Workbench E QC / diagnostics | `derive_matrix_script_qc_diagnostics_view` | gateway/app/services/matrix_script/qc_diagnostics_view.py |
| 13 | Workbench E delivery-ready package teaser | `derive_matrix_script_delivery_ready_package` | gateway/app/services/matrix_script/delivery_ready_package_view.py |
| 14 | Workbench F delivery link / readiness teaser | `derive_matrix_script_delivery_comprehension` + `compute_publish_readiness.publishable` | gateway/app/services/matrix_script/delivery_comprehension.py + publish_readiness producer |
| 15 | Delivery Center final_video primary | `derive_matrix_script_delivery_comprehension.final_video_primary` + L3 `final_provenance` (Recovery PR-1 emitter) | gateway/app/services/matrix_script/delivery_comprehension.py + Recovery PR-1 emitter |
| 16 | Delivery Center required deliverables | `factory_delivery_contract_v1` `required` / `blocking_publish` per Plan C amendment | [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) |
| 17 | Delivery Center optional scene_pack (non-blocking) | `SCENE_PACK_BLOCKING_ALLOWED = False` constant in delivery_binding.py | gateway/app/services/matrix_script/delivery_binding.py |
| 18 | Delivery Center copy bundle | `derive_matrix_script_delivery_copy_bundle` | gateway/app/services/matrix_script/delivery_copy_bundle_view.py |
| 19 | Delivery Center publish readiness banner | `compute_publish_readiness` | publish_readiness producer (Recovery PR-1) |
| 20 | Delivery Center publish feedback rows | Phase D.0 closure `variation_feedback[]` | gateway/app/services/matrix_script/publish_feedback_closure.py |
| 21 | Publish Feedback event log | `feedback_closure_records[]` | same |
| 22 | Publish Feedback metrics snapshot | `channel_metrics` (closed key set) | same |
| 23 | Iteration hint | `derive_matrix_script_publish_backfill_readiness` | gateway/app/services/matrix_script/publish_backfill_readiness_view.py |
| 24 | Archive marker | `record_kind == "archive_action"` event | publish_feedback_closure.py |
| 25 | Cross-line publishable truth | `publish_readiness_contract_v1` (single producer) | [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md) |
| 26 | Cross-line provenance | L3 `final_provenance` amendment | [docs/contracts/hot_follow_current_attempt_contract_v1.md](../contracts/hot_follow_current_attempt_contract_v1.md) §"final_provenance" |
| 27 | Cross-line workbench panel dispatch | `workbench_panel_dispatch_contract_v1` `panel_kind == "matrix_script"` | [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) |
| 28 | Cross-line advisory taxonomy | `l4_advisory_producer_output_contract_v1` | [docs/contracts/l4_advisory_producer_output_contract_v1.md](../contracts/l4_advisory_producer_output_contract_v1.md) |

---

## 9. Backend / runtime mapping (UI → existing object) — per-block summary

The full per-block mapping lives in §8 and in each wireframe. This section is a one-paragraph narrative mapping for a reader who wants the punchline without scanning the table.

- The **Task Area card body** is a render of `derive_matrix_script_task_card_summary` (8 fields), `derive_matrix_script_eight_stage_state` (badge), `derive_matrix_script_three_tier_lanes` (three lanes), and `derive_matrix_script_task_area_result_status` (status pill + next-action chip). All four exist already.
- The **Workbench** is composed of pure projections over the Phase A entry, Phase B variation_matrix + slot_pack, Phase C delivery binding, and Phase D.0 closure. The result-oriented wave's job is to *re-arrange* those projections into the six blocks A..F — not to add new state.
- The **Delivery Center** is a render of `derive_matrix_script_delivery_comprehension` (lanes + final_video primary), `derive_matrix_script_delivery_copy_bundle` (copy lane), and `derive_matrix_script_delivery_ready_package` (per-deliverable readiness). Publish readiness is the single output of `compute_publish_readiness`.
- The **Publish Feedback** sub-zone is a direct render of the Phase D.0 closure object plus the existing `POST /api/matrix-script/closures/{task_id}/events` endpoint with the closed enums `D1_EVENT_KINDS`, `D1_PUBLISH_STATUS_VALUES`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES`. The same endpoint receives operator notes from Workbench Block E.

---

## 10. Hot Follow as UX benchmark (not file touch)

Hot Follow is the runtime reference line per [alignment map §2.6](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). The UX benchmark this design package borrows from Hot Follow is **operator readability**, not file structure. Concretely:

- Hot Follow's workbench surface foregrounds **what to do next** in operator language (built from `hot_follow_route_state.build_hot_follow_current_attempt_summary` + ready-gate). Matrix Script's `derive_matrix_script_recommended_action` + `derive_matrix_script_workbench_result_summary` mirror the same pattern.
- Hot Follow's publish hub renders a single primary `final.mp4` slot with provenance label (`current` / `historical`). Matrix Script Delivery Center mirrors this with its `final_video` primary + `final_provenance` label (gap noted in §11 — primary slot exists, provenance label currently inferred not L3-emitted).
- Hot Follow exposes advisories as operator-language guidance, not validator messages. Matrix Script Block E + Workbench banner consumes the same `l4_advisory_producer_output_contract_v1` shape (gap noted in §11 — producer service is contract-only).

No Hot Follow file is touched by this design package. The benchmark is a behaviour reference; the implementation surface is independent per recovery amendment §7.

---

## 11. Explicit gap list

Each gap is classified `backend gap` / `presenter gap` / `interaction gap`. None of these are solved in this step — the recovery wave already shipped the substrate, and the alignment map's frozen sequence governs when each gap is closed.

### 11.1 backend gap (data not yet emitted by any service)

| ID | Gap | Symptom in UI | Closure path |
|---|---|---|---|
| BG-1 | L4 advisory producer service not yet emitting | Workbench Block E "advisory strip" renders empty list; Delivery Center publish readiness banner cannot show a `recommended_next_action` text from L4 | `l4_advisory_producer_output_contract_v1` already frozen — producer implementation deferred to Plan E (alignment map §7.3) |
| BG-2 | L3 `final_provenance` emitted as inferred label, not first-class field on Matrix Script | Delivery Center final_video primary cannot show a definitive `current` vs `historical` badge; today the badge is derived from RC PR-1 substrate but not emitted per L3 contract | Recovery PR-1 emitter exists for projection-side; full first-class L3 field on packet remains gated to Plan E (per [hot_follow_current_attempt_contract_v1](../contracts/hot_follow_current_attempt_contract_v1.md) §"final_provenance") |
| BG-3 | Per-variation final media artifact link not yet resolved by `result_packet_binding.artifact_lookup` for non-`final_video` rows | Workbench Block E's per-variant cards show "tracked-gap" text in place of a real preview link for subtitle / audio / pack rows | E.MS.1 (Plan E PR-1) closed `final_video` slot; subtitle / audio / pack lookups remain gap |
| BG-4 | `metrics_snapshot` raw payload reference | Publish Feedback "raw payload" link cannot be opened — currently `raw_payload_ref` is a contract field but no resolver exists | future Plan E phase |
| BG-5 | Iteration recommendation grounded in metrics history | Iteration hint at Delivery Center renders a static "consider regenerating low-engagement variants" placeholder; no actual metric-grounded recommendation | future post-Plan-E wave (analytics) |

### 11.2 presenter gap (data exists but not yet projected to operator language)

| ID | Gap | Symptom in UI | Closure path |
|---|---|---|---|
| PG-1 | `head_reason` operator label coverage for less-common values | When `head_reason ∈ {final_provenance_historical, required_deliverable_blocking}` the operator label may fall back to a generic "未就绪" string | extend `HEAD_REASON_LABELS_ZH` in a follow-on presenter-only PR (no contract change) |
| PG-2 | Per-variant differentiator text quality | Variant Strategy block (Workbench C) renders axis-tuple labels that may still be developer-language for unusual axis kinds | extend `derive_matrix_script_readable_variants` axis-tuple → operator-label dictionary |
| PG-3 | Blocker → next-action text mapping for closure-D.1 retracted state | Task Area "current blocker" may render `retracted` in raw English | add operator label in `result_status_view.py` |
| PG-4 | Archive operator-language hint | Task Area card archive badge currently renders "已归档" with no iteration-hint trailer | derive trailer from `derive_matrix_script_publish_backfill_readiness` next-iteration-text |
| PG-5 | `evidence.reference_line` exposure on operator surfaces | Reference badge `hot_follow ✓` exists in surface low-fi but is not yet rendered on Matrix Script result-oriented blocks | trivial template addition (no service change) |

### 11.3 interaction gap (UX affordance not yet wired)

| ID | Gap | Symptom | Closure path |
|---|---|---|---|
| IG-1 | "Open publish feedback" jump from Task Area card | Card has `Open delivery` but no `Open publish feedback` direct anchor | template anchor `#publish-feedback` already present; add second button row in card |
| IG-2 | "Regenerate blocked variant" per-variant action | Workbench Block E exposes "submit zone-scoped review" but not a single-button "regenerate this variant" action | requires routing the existing variation execution path scoped by `cell_id`; design covered in [workbench wireframe §"D. Generate / Regenerate Action Block"](matrix_script_workbench_wireframe_v1.md) |
| IG-3 | Iteration "launch next iteration" affordance | Task Area archived card has no one-click "duplicate as new task" affordance | future Plan E phase or operator-tooling wave |
| IG-4 | Block E recommended-candidate confirmation event | Picking a candidate currently posts an `operator_note` event but does not transition any closed state — design wants it to advance `STAGE_AWAITING_REVIEW → STAGE_FINAL_READY` | future closure D.1 enrichment (additive event semantics, not enum widening) |
| IG-5 | Inline "preview / play" for `final_video` primary slot | Delivery Center primary slot renders a thumbnail + label but no inline player; operators jump to R2/CDN URL | future Plan E phase |

---

## 12. Hard constraints (binding for any future implementation that consumes this design)

1. No vendor / model / provider / engine selection in any operator-visible UI for this line.
2. No raw `content://` handle, `cell_id`, `slot_id`, ref counter, validator report drawer in operator-visible surfaces. (Inspector views remain available behind a non-operator route, out of scope for this design.)
3. `final_video` is the primary deliverable slot. Supporting deliverables are subtitle, audio, copy_bundle, metadata, manifest, scene_pack (optional), publish_status. No other bundle item is promoted to primary.
4. Scene Pack is non-blocking. `SCENE_PACK_BLOCKING_ALLOWED = False` is binding; operators may always advance other capabilities while scene_pack is incomplete.
5. Operators must not author packet truth on any surface this design covers in this wave. Phase B authoring affordance is system-only per Plan E gate spec §4.3.
6. Every operator-language label originates from an existing closed enum or projection helper; designs may not invent new state vocabulary.
7. No second truth source. Any block claiming `publishable` must consume `compute_publish_readiness` directly (RC-A7).
8. No fake `final_video` / no fabricated `publish_url` (RC-R8). Empty-state rows render as explicit tracked-gap with operator-language text, not as fake links.
9. No Digital Anchor / Hot Follow / Asset Supply file is touched by anything that follows from this design.
10. Implementation gate remains as defined by the alignment map's frozen next engineering sequence; this design package does not open it.

---

## 13. Implementation boundary (binding)

This design package is **frontend design only**. Specifically:

- No runtime wiring is added.
- No backend implementation is added.
- No contract is authored, widened, or amended.
- No schema is rewritten.
- No Digital Anchor work is touched.
- No template, service, route, or test file is changed by this PR.

A future implementation PR consuming this design must:

- Cite this document in its reading declaration.
- Cite the relevant wireframe (Task Area / Workbench / Delivery Center) in its reading declaration.
- Cite the implementation slicing addendum [matrix_script_result_oriented_ui_implementation_slicing_v1.md](matrix_script_result_oriented_ui_implementation_slicing_v1.md) and observe its §2 pre-conditions and §9 cross-PR discipline.
- Cite the recovery gate spec [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md) and observe its §4 forbidden scope.
- Open under whatever wave authority is current at the time (per the alignment map §3.3 allowed engineering actions for that wave).
- Update §11 of this document only by appending — never silently retire a gap entry without a follow-on docs-only PR.

### 13.1 Recommended PR slicing reference

The recommended four-PR slicing (PR-1 Task Area card refit → PR-2 Workbench Blocks A / B / C → PR-3 Workbench Blocks D / E / F → PR-4 Delivery Center A–F + Publish Feedback → Closeout) for the future implementation wave is captured in [matrix_script_result_oriented_ui_implementation_slicing_v1.md](matrix_script_result_oriented_ui_implementation_slicing_v1.md). Each slice is annotated with operator-visible outcome, backend feeds consumed, secondary diagnostics scope, acceptance evidence, and hard non-goals. That addendum does not open the implementation gate; the alignment map's frozen next engineering sequence governs when it does.

---

## 14. Reading declaration consumed in authoring this document

- Bootloader: [CLAUDE.md](../../CLAUDE.md), [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) (esp. §6 Contract-First, §8 Truth-Source, §13 Product-Flow Module Presence), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md).
- Alignment map: [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §§2 / 3 / 4.2 / 6 / 7.
- Product authority: [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md).
- Recovery authority: [docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md](../product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md), [docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md](../reviews/matrix_script_result_capability_recovery_gate_spec_v1.md), [docs/execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_MATRIX_SCRIPT_RESULT_CAPABILITY_RECOVERY_CLOSEOUT_v1.md).
- Surface authority: [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](ApolloVeo_Operator_Visible_Surfaces_v1.md), [docs/design/surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md), [docs/design/surface_workbench_lowfi_v1.md](surface_workbench_lowfi_v1.md), [docs/design/surface_delivery_center_lowfi_v1.md](surface_delivery_center_lowfi_v1.md), [docs/design/panel_matrix_script_variation_lowfi_v1.md](panel_matrix_script_variation_lowfi_v1.md).
- Line contracts (consulted): [docs/contracts/matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md), [task_entry_contract_v1](../contracts/matrix_script/task_entry_contract_v1.md), [variation_matrix_contract_v1](../contracts/matrix_script/variation_matrix_contract_v1.md), [slot_pack_contract_v1](../contracts/matrix_script/slot_pack_contract_v1.md), [workbench_variation_surface_contract_v1](../contracts/matrix_script/workbench_variation_surface_contract_v1.md), [delivery_binding_contract_v1](../contracts/matrix_script/delivery_binding_contract_v1.md), [publish_feedback_closure_contract_v1](../contracts/matrix_script/publish_feedback_closure_contract_v1.md), [result_packet_binding_artifact_lookup_contract_v1](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md).
- Cross-line contracts (consulted): [factory_packet_envelope_contract_v1](../contracts/factory_packet_envelope_contract_v1.md), [factory_packet_validator_rules_v1](../contracts/factory_packet_validator_rules_v1.md), [factory_delivery_contract_v1](../contracts/factory_delivery_contract_v1.md), [publish_readiness_contract_v1](../contracts/publish_readiness_contract_v1.md), [l4_advisory_producer_output_contract_v1](../contracts/l4_advisory_producer_output_contract_v1.md), [workbench_panel_dispatch_contract_v1](../contracts/workbench_panel_dispatch_contract_v1.md).
- Service surveyed (read-only): `gateway/app/services/matrix_script/` (`task_area_convergence.py`, `task_card_summary.py`, `result_status_view.py`, `workbench_comprehension.py`, `script_structure_view.py`, `readable_variant_view.py`, `recommended_action_view.py`, `preview_compare_view.py`, `review_zone_view.py`, `qc_diagnostics_view.py`, `delivery_comprehension.py`, `delivery_copy_bundle_view.py`, `delivery_backfill_view.py`, `delivery_ready_package_view.py`, `publish_backfill_readiness_view.py`, `publish_feedback_closure.py`, `closure_binding.py`, `delivery_binding.py`).

This document is documentation only.
