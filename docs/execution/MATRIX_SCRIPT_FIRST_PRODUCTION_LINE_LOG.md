# Matrix Script First Production Line — Execution Log

Active execution log for the Matrix Script First Production Line Wave
(`docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md`).

This wave is gated to a single line (`matrix_script`) and a single closure shape:
`task → workbench → delivery → publish feedback`. Phases A–D are sequenced and
strictly non-overlapping; each phase is reviewable independently.

---

## Phase A — Task Entry

- Date: 2026-04-27
- Status: implementation green (docs-first / surface-first); awaiting architect + reviewer signoff
- Authority:
  - 指挥单 §6 Phase A (target, minimum scope, acceptance)
  - `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
  - `schemas/packets/matrix_script/packet.schema.json`
  - `docs/product/asset_supply_matrix_v1.md` (matrix_script row)
  - `docs/design/surface_task_area_lowfi_v1.md`
- Evidence: `docs/execution/evidence/matrix_script_phase_a_task_entry_v1.md`
- Code / docs:
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (NEW — Phase A surface contract)
  - `docs/execution/evidence/matrix_script_phase_a_task_entry_v1.md` (NEW — Phase A evidence)
  - `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` (NEW — this log)
  - `docs/execution/apolloveo_2_0_evidence_index_v1.md` (UPDATED — Phase A row added)
  - `tests/contracts/matrix_script/__init__.py` (NEW)
  - `tests/contracts/matrix_script/test_task_entry_phase_a.py` (NEW — Phase A validation suite)
- What this phase adds:
  - Closed entry-field set for the Matrix Script task entry: `topic`, `source_script_ref`,
    `language_scope`, `target_platform`, `variation_target_count`, `audience_hint`,
    `tone_hint`, `length_hint`, `product_ref`, `operator_notes`.
  - Per-field classification: line truth (`source_script_ref`, `language_scope`) vs
    operator hint (everything else).
  - Per-field discipline: required at entry vs optional vs deferred.
  - Entry → packet mapping rule. Only `source_script_ref` and `language_scope` cross
    to packet truth (line-specific delta). Other entries map to `metadata.notes` or to
    Phase B authoring scaffolding; no entry mutates a closed kind-set.
  - Explicit deferral table for Phase B / Phase C / Phase D / never.
  - Explicit forbidden-field list at entry surface (vendor / model / provider / engine,
    truth-shape state fields, donor-side concepts, cross-line concerns).
  - Phase A validation tests: presence, closed entry-field set, mapping reachability,
    no forbidden tokens, no truth-shape fields, no out-of-wave scope.
- What this phase does NOT add: no workbench variation authoring, no delivery
  binding, no publish feedback, no provider/adapter touch, no Digital Anchor entry,
  no Hot Follow change, no W2.2 / W2.3 advancement, no packet/schema/sample
  re-version, no frontend platform rebuild, no runtime task-creation code.
- Hard stop: after Phase A, do not start Phase B. Wait for explicit next instruction.

---

## Phase B — Workbench Variation Surface

- Date: 2026-04-27
- Status: implementation green (contract-first / projection-only); awaiting architect + reviewer signoff
- Authority:
  - 指挥单 §7 Phase B (target, minimum scope, acceptance)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A entry seed boundary)
  - `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
  - `schemas/packets/matrix_script/packet.schema.json`
  - `schemas/packets/matrix_script/sample/*.json`
  - `docs/design/panel_matrix_script_variation_lowfi_v1.md`
  - `docs/design/surface_task_area_lowfi_v1.md`
- Evidence: `docs/execution/evidence/matrix_script_phase_b_workbench_variation_surface_v1.md`
- Code / docs:
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (NEW — Phase B surface contract)
  - `docs/execution/evidence/matrix_script_phase_b_workbench_variation_surface_v1.md` (NEW — Phase B evidence)
  - `gateway/app/services/matrix_script/workbench_variation_surface.py` (NEW — read-only packet projection)
  - `gateway/app/services/matrix_script/__init__.py` (NEW)
  - `gateway/app/routers/matrix_script_panel_debug.py` (UPDATED — debug panel consumes formal projection)
  - `tests/contracts/matrix_script/test_workbench_variation_phase_b.py` (NEW — Phase B validation suite)
- What this phase adds:
  - Formal Workbench Variation Surface projection object:
    `variation_plan`, `copy_bundle`, `slot_detail_surface`, `attribution_refs`,
    `publish_feedback_projection`, plus legacy preview aliases for the current
    lightweight debug panel.
  - Variation matrix surface derived only from
    `line_specific_refs[matrix_script_variation_matrix].delta`: `axis_kind_set`,
    `axes`, and `cells`.
  - Slot detail surface derived only from
    `line_specific_refs[matrix_script_slot_pack].delta`: `slot_kind_set` and `slots`,
    joined by `variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id`.
  - Attribution / refs projection from packet provenance only: `generic_refs`,
    `line_specific_refs`, `binding.capability_plan`, and `binding.worker_profile_ref`.
  - Publish feedback projection as read-only context only: `reference_line`,
    `validator_report_path`, `ready_state`, and `feedback_writeback =
    not_implemented_phase_b`.
  - Phase B validation tests for contract presence, sample projection fidelity,
    slot join integrity, attribution boundary, publish feedback read-only boundary,
    packet immutability, and forbidden-scope absence.
- What this phase does NOT add: no delivery binding, no publish feedback write-back,
  no provider/model/vendor controls, no packet/schema redesign, no Digital Anchor,
  no Hot Follow change, no W2.2 / W2.3 advancement, no heavy frontend rebuild,
  and no formal runtime API commitment beyond the existing debug preview route.
- Hard stop: after Phase B, do not start Phase C. Wait for review / next instruction.

## Phase C — Delivery Binding

- Date: 2026-04-28
- Status: implementation green (contract-first / projection-only); awaiting architect + reviewer signoff
- Authority:
  - 指挥单 Phase C (target, minimum scope, acceptance)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A entry boundary)
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (Phase B workbench boundary)
  - `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
  - `schemas/packets/matrix_script/packet.schema.json`
  - `schemas/packets/matrix_script/sample/*.json`
  - `docs/contracts/factory_delivery_contract_v1.md`
- Evidence: `docs/execution/evidence/matrix_script_phase_c_delivery_binding_v1.md`
- Code / docs:
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (NEW — Phase C delivery contract)
  - `docs/execution/evidence/matrix_script_phase_c_delivery_binding_v1.md` (NEW — Phase C evidence)
  - `gateway/app/services/matrix_script/delivery_binding.py` (NEW — read-only delivery projection)
  - `gateway/app/services/matrix_script/__init__.py` (UPDATED — export delivery projector)
  - `gateway/app/routers/matrix_script_panel_debug.py` (UPDATED — read-only `/delivery-data`)
  - `tests/contracts/matrix_script/test_delivery_binding_phase_c.py` (NEW — Phase C validation suite)
- What this phase adds:
  - Formal Delivery Binding projection object:
    `delivery_pack`, `result_packet_binding`, `manifest`, `metadata_projection`,
    and `phase_d_deferred`.
  - Visible delivery-center rows for Matrix Script:
    `matrix_script_variation_manifest`, `matrix_script_slot_bundle`,
    `matrix_script_subtitle_bundle`, `matrix_script_audio_preview`, and
    `matrix_script_scene_pack`.
  - `result_packet_binding` visualization from packet truth only: generic refs,
    line-specific refs, binding profile refs, capability plan, and cell-to-slot
    bindings from `variation_matrix.delta.cells[]` joined to `slot_pack.delta.slots[]`.
  - Manifest / metadata behavior as read-only display projection from packet identity,
    binding refs, packet metadata, and validator report path.
  - Phase C validation tests for contract presence, deliverable projection,
    result binding projection, manifest/metadata read-only behavior, Phase D feedback
    deferral, packet immutability, and forbidden-scope absence.
- What this phase does NOT add: no publish feedback write-back, no provider/model/vendor
  controls, no packet/schema redesign, no Digital Anchor, no Hot Follow change,
  no W2.2 / W2.3 advancement, no frontend heavy rebuild, no artifact lookup,
  and no runtime/provider orchestration.
- Hard stop: after Phase C, do not start Phase D. Wait for review / next instruction.

## Phase D — Publish Feedback Closure

### Phase D.0 — Contract Freeze

- Date: 2026-04-28
- Status: contract freeze landed (no implementation); awaiting architect + reviewer signoff
- Phase C signoff input: PASS (per total-control instruction issued 2026-04-28)
- Authority:
  - 指挥单 Phase D (target, minimum scope, acceptance)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A boundary)
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (Phase B boundary)
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (Phase C boundary)
  - `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
  - `schemas/packets/matrix_script/packet.schema.json`
- Evidence: `docs/execution/evidence/matrix_script_phase_d_publish_feedback_closure_contract_v1.md`
- Code / docs:
  - `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` (NEW — Phase D.0 contract freeze)
  - `docs/execution/evidence/matrix_script_phase_d_publish_feedback_closure_contract_v1.md` (NEW — Phase D.0 evidence)
  - `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` (UPDATED — this row)
  - `docs/execution/apolloveo_2_0_evidence_index_v1.md` (UPDATED — Phase D contract + evidence rows)
- What this phase adds:
  - Formal Publish Feedback Closure object `matrix_script_publish_feedback_closure_v1`
    with `closure_id`, `line_id`, `packet_version`, `variation_feedback[]`, and
    `feedback_closure_records[]`.
  - Variation-level feedback row shape: `variation_id`, `publish_url`,
    `publish_status` ∈ `{pending, published, failed, retracted}`, `channel_metrics`,
    `operator_publish_notes`, `last_event_id`.
  - Closed `channel_metrics` snapshot keys: `channel_id`, `captured_at`,
    `impressions`, `views`, `engagement_rate`, `completion_rate`, `raw_payload_ref`.
  - Append-only `feedback_closure_records[]` audit trail keyed by `event_id` with
    `event_kind` ∈ `{operator_publish, operator_retract, operator_note,
    platform_callback, metrics_snapshot}` and `actor_kind` ∈
    `{operator, platform, system}`.
  - Explicit ownership and mutability rules; explicit boundary vs Phase A/B/C.
  - Canonical variation-id join rule:
    `packet.line_specific_refs[matrix_script_variation_matrix].delta.cells[].cell_id`
    ↔ `variation_feedback[].variation_id`.
  - Mapping note from Phase C delivery projection fields to Phase D closure fields,
    with explicit operator-action vs platform-callback origin.
  - Explicit out-of-scope list (no per-deliverable feedback, no provider controls,
    no Digital Anchor, no Hot Follow, no W2.2 / W2.3, no packet schema change,
    no write-back implementation).
- What this phase does NOT add:
  - no write-back implementation code (no changes under `gateway/`);
  - no schema / sample / packet contract change;
  - no change to Phase A/B/C contracts;
  - no delivery projector mutation;
  - no manifest or metadata projection ownership mutation;
  - no provider / model / vendor / engine controls;
  - no Digital Anchor;
  - no Hot Follow;
  - no W2.2 / W2.3 advancement;
  - no tests added (contract-freeze wave; review-only validation).
- Hard stop: after Phase D.0, do not start Phase D.1 implementation. Wait for
  review / next instruction.

### Phase D.1 — Minimal Publish Feedback Closure Write-Back

- Date: 2026-04-28
- Status: implementation green (minimal write-back); awaiting architect + reviewer signoff
- Phase D.0 signoff input: PASS (per total-control instruction issued 2026-04-28)
- Authority:
  - 指挥单 Phase D (target, minimum scope, acceptance)
  - `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` (Phase D.0 freeze)
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (Phase C boundary)
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (Phase B boundary)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A boundary)
  - `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
  - `schemas/packets/matrix_script/packet.schema.json`
- Evidence: `docs/execution/evidence/matrix_script_phase_d1_publish_feedback_closure_writeback_v1.md`
- Code / docs:
  - `gateway/app/services/matrix_script/publish_feedback_closure.py` (NEW — minimal closure persistence and append-only event surface)
  - `gateway/app/services/matrix_script/__init__.py` (UPDATED — export closure entry points)
  - `tests/contracts/matrix_script/test_publish_feedback_closure_phase_d1.py` (NEW — Phase D.1 validation suite)
  - `tests/contracts/matrix_script/test_task_entry_phase_a.py` (UPDATED — phase-sequence assertion advanced from "Phase D NOT STARTED" to "Phase D.0 contract freeze + Phase D.1 implementation row")
  - `docs/execution/evidence/matrix_script_phase_d1_publish_feedback_closure_writeback_v1.md` (NEW — Phase D.1 evidence)
  - `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` (UPDATED — this row)
  - `docs/execution/apolloveo_2_0_evidence_index_v1.md` (UPDATED — Phase D.1 evidence + tests rows)
- What this phase adds:
  - In-process persistence surface for `matrix_script_publish_feedback_closure_v1`
    seeded one row per `cell_id` from
    `line_specific_refs[matrix_script_variation_matrix].delta.cells[]`.
  - Variation-level write-back via the canonical `cell_id ↔ variation_id`
    join with closed enum enforcement on `publish_status`, `event_kind`,
    `actor_kind`, and `channel_metrics` keys.
  - Append-only `feedback_closure_records[]` with per-event
    `event_id`, `recorded_at`, `actor_kind`, `payload_ref`, and
    `last_event_id` pointer maintained on each `variation_feedback[]` row.
  - Origin-rule enforcement: operator-only `pending` / `retracted`,
    platform-only `published` / `failed`, metrics-snapshot-only
    `channel_metrics` writes, operator-note-only `operator_publish_notes`
    writes.
  - Phase D.1 validation tests covering closure creation, packet
    immutability, each event-kind path, append-only audit growth,
    in-memory store isolation, the Phase C read-only invariant, and
    forbidden-scope absence.
- What this phase does NOT add:
  - no durable persistence backend (database / queue / file);
  - no HTTP / WebSocket / callback-handler transport;
  - no provider / model / vendor / engine controls;
  - no per-deliverable feedback (variation-level only);
  - no multi-channel arbitration or routing policy;
  - no analytics aggregation, dashboards, or cross-line rollup;
  - no ACL / auth model for closure mutation;
  - no additive `schemas/feedback/matrix_script/*.schema.json` file
    (deferred to the durable-persistence wave);
  - no change to Phase A / B / C contracts, the Matrix Script packet,
    schema, sample, the workbench projector, or the delivery projector;
  - no Digital Anchor scope;
  - no Hot Follow scope;
  - no W2.2 / W2.3 advancement;
  - no frontend rebuild;
  - no debug-panel mutation.
- Hard stop: after Phase D.1, do not auto-start Digital Anchor. Wait for
  Matrix Script line signoff and explicit next instruction.

### Formal Create-Entry Alignment — Matrix Script Only

- Date: 2026-05-02
- Status: implementation green; awaiting review/signoff
- Evidence: `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md`
- Code / docs:
  - `gateway/app/services/matrix_script/create_entry.py` (NEW — Matrix Script create-entry payload builder)
  - `gateway/app/routers/tasks.py` (UPDATED — formal Matrix Script GET/POST create route; Matrix removed from temporary connected create map)
  - `gateway/app/templates/matrix_script_new.html` (NEW — formal Matrix Script create-entry page)
  - `gateway/app/templates/tasks_newtasks.html` (UPDATED — Matrix Script card targets formal route)
  - `gateway/app/services/tests/test_new_tasks_surface.py` (UPDATED — route, form, redirect, and temporary-path assertions)
  - `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md` (NEW — this wave evidence)
- What this wave adds:
  - formal Matrix Script create-entry route at `/tasks/matrix-script/new`;
  - closed Matrix Script create-input form matching `task_entry_contract_v1`;
  - repository task payload with `kind/category_key/platform=matrix_script`;
  - Matrix `line_specific_refs[]` seed so the existing workbench line panel can mount;
  - task creation redirect to `/tasks/{task_id}`;
  - existing delivery transition remains `/tasks/{task_id}/publish`.
- What this wave removes from the primary path:
  - `/tasks/connect/matrix_script/new` is no longer a valid Matrix Script create-entry path.
- What this wave does NOT add:
  - no Digital Anchor implementation;
  - no Hot Follow change;
  - no Board redesign;
  - no Delivery redesign;
  - no B-roll;
  - no packet/schema redesign;
  - no provider / model / vendor / engine controls;
  - no `/debug/panels/...` operator entry;
  - no language logic change or target-language expansion.
- Hard stop: complete Matrix Script only. Do not auto-start Digital Anchor.
  Wait for review/signoff.
