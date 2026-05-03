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

### Plan A Trial Correction §8.H — Operator Brief Re-correction (Binding Product-Meaning of `source_script_ref`, Documentation-only)

- Date: 2026-05-03
- Status: documentation correction green; ready for signoff
- Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §8 (Recommended Ordering — §8.H natural successor); explicit user instruction landing §8.H ("expand §8.H slightly to also explain the product meaning of `source_script_ref`: asset identity handle, not body-input field, not publisher-URL ingestion field, not currently dereferenced content address. Matrix Script live-run remains BLOCKED until §8.H lands."); `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (operator-facing trial brief — re-corrected by this change); `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` (trial coordinator write-up — extended by a §12 addendum); `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (§8.A — landed); `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (§8.B — confirmed); `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (§8.C — landed); `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` (§8.D — landed); `docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md` (§8.G — landed); `docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md` (§8.E — landed); `docs/execution/MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md` (§8.F — landed)
- Execution log: `docs/execution/MATRIX_SCRIPT_H_OPERATOR_BRIEF_RECORRECTION_EXECUTION_LOG_v1.md`
- Doc changes:
  - `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (UPDATED — refreshed front-matter date / status / authority list; expanded §0.1 binding sample-validity rule from 4 criteria to 7 explicitly-numbered criteria — formal create-entry route; §8.A + §8.F opaque-ref shape (four-scheme set `content`/`task`/`asset`/`ref` only); §8.F operator transitional convention `content://matrix-script/source/<token>`; §8.C populated Phase B truth; §8.B + §8.G mounted readable Phase B panel with human-readable Axes-table values asserted; §8.E shared-shell suppression with closed forbidden-token list enumerated; §8.D + §8.H operator brief in force; new explicit rule that pre-§8.F publisher-URL / bucket-URI samples (including live-trigger `task_id=415ea379ebc6`) are invalid evidence; ADDED new §0.2 "Product Meaning of `source_script_ref` (binding, §8.H)" section — four-bullet load-bearing structure (what it IS: source-script asset identity handle; what it IS NOT × 3: NOT body-input field, NOT publisher-URL ingestion field, NOT currently dereferenced content address) plus why-it-matters paragraph and forward-compatibility statement for Plan E Option F2; refreshed §3.1 Matrix Script row, §3.2 create-entry / Workbench / Delivery rows, §3.3 inspect-only list with new shared-shell row, §5.2 Workbench explanation 口径 with three new coordinator notes (§8.G repr, §8.E shell, §8.F rejection), §6.2 Matrix Script line guidance end-to-end (product-meaning preamble, §8.A + §8.F sample profile, §8.G Axes-table render shape, §8.E shared-shell visible-HTML shape, §8.C Phase B truth, extended operator-misuse bullets), §7.1 sample 3 (transitional convention example, HTTP 400 rejection callouts, §0.2 citation, six goals (a)–(f) including §8.G + §8.E criteria), §7.2 samples-to-avoid (three new bullets), §8 risk list (six new rows covering publisher-URL / bucket-URI submission, pre-§8.F sample reuse, bound-method repr observation, Hot Follow controls observation, `source_script_ref` product-meaning confusion, Plan E forward-compatibility concern), §11.1 corrections-landed history (five new rows for follow-up review filing + §8.G + §8.E + §8.F + §8.H), §12 Final Readiness Conclusion (eight conditions; full §8.A–§8.H PASS list; explicit live-run unblock by virtue of §8.H land))
  - `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` (UPDATED — appended new §"12. Matrix Script Plan A Trial Follow-up Corrections — Addendum (2026-05-03)" after the existing §11 §8.D addendum; sub-sections §12.1 (why §11 was insufficient — three observed defects on `task_id=415ea379ebc6`), §12.2 trial-corrections-landed-status table for §8.G / §8.E / §8.F / §8.H, §12.3 static-pass overlay with coordinator verification recipes (grep for `<built-in method values`, grep for the closed Hot Follow control token list with `<script>` blocks stripped, attempt a publisher-URL POST in a non-operator environment to expect 400), §12.4 coordinator action items extending §11.4 with §0.2-product-meaning-verbatim briefing requirement, §12.5 final corrected judgment with the post-§8.H gate state)
  - `docs/execution/MATRIX_SCRIPT_H_OPERATOR_BRIEF_RECORRECTION_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - operator-facing documentation now reflects the full accepted §8.A / §8.B / §8.C / §8.D / §8.E / §8.F / §8.G chain; the §0.1 sample-validity rule is the binding seven-criterion gate; the new §0.2 product-meaning section is binding and explicitly states the three "is NOT" clauses; the §6.2 Matrix Script line guidance is self-contained with a duplicated product-meaning preamble; the §7.1 / §7.2 / §8 / §11.1 / §12 rows close the documentation chain;
  - explicit valid vs invalid Matrix Script trial sample criteria pinned at the operator brief §0.1 level (post-§8.A / §8.B / §8.C / §8.D / §8.E / §8.F / §8.G);
  - explicit risk-list coverage for publisher-URL / bucket-URI submission, pre-§8.F sample reuse, bound-method repr observation, Hot Follow shell-controls observation on a Matrix Script workbench, `source_script_ref` product-meaning confusion, and Plan E forward-compatibility concern;
  - inspect-only / contract-only boundaries preserved verbatim: Matrix Script Delivery Center stays inspect-only (Plan B B4 / `result_packet_binding_artifact_lookup_contract_v1`); Matrix Script Phase D.1 publish-feedback closure surface stays as already shipped per `publish_feedback_closure_contract_v1`;
  - Matrix Script live-run BLOCK released by virtue of §8.H land, subject to the eight conditions enumerated in the trial brief §12.
- What this correction does NOT add:
  - no runtime behavior change — no `.py`, no `.html`, no schema, no sample, no contract, no template, no test edits;
  - no contract change — no edits to any `docs/contracts/**` file (including the §8.A / §8.C / §8.F addenda on `task_entry_contract_v1` and the §8.E `Shared shell neutrality` addendum on `workbench_panel_dispatch_contract_v1`);
  - no `PANEL_REF_DISPATCH` widening; no schema / sample / packet re-version;
  - no §8.A / §8.B / §8.C / §8.D / §8.E / §8.F / §8.G reopening; no workbench redesign;
  - no Hot Follow / Digital Anchor scope reopening; no Runtime Assembly / Capability Expansion entry;
  - no provider / model / vendor / engine controls;
  - no Plan E gated items (B4, D1, D2, D3, D4, Digital Anchor B1 / B2 / B3 implementation; F2 in-product minting flow);
  - no second production line onboarding; no Asset Library / promote (Plan C C1–C3) work;
  - no live-trial execution (operations team appends live-run results to `PLAN_A_OPS_TRIAL_WRITEUP_v1.md` §8 separately);
  - no backwards-compatibility shim for tasks created under any pre-correction state — pre-§8.A pasted-body samples and pre-§8.F publisher-URL / bucket-URI samples (including the live-trigger sample `task_id=415ea379ebc6`) all remain invalid evidence;
  - no `g_lang` token alphabet pinning;
  - no CSS-only operator hint — the operator brief lives in the document body; coordinator briefs operators verbatim before any sample-creation session.
- Validation: documentation-only change; per `ENGINEERING_RULES.md` §10 there is no runtime regression to run; the §8.A / §8.B / §8.C / §8.D / §8.E / §8.F / §8.G suites remain green on baseline `3d82784` (post-§8.F / PR #90 merge to main) and are not affected (no code edited); cross-checks recorded in §4.2 of the §8.H execution log confirm the brief and write-up consume §8.A's accepted-scheme-set verbatim, §8.F's tightened-scheme-set verbatim, §8.B's captured render markers verbatim, §8.C's deterministic axes / cells / slots / `body_ref` template verbatim, §8.G's human-readable Axes-table render shape verbatim, §8.E's closed forbidden-token list verbatim, the Plan B B4 inspect-only Delivery Center boundary, and the Phase D.1 closure surface boundary; surrounding-suite sanity check 200/200 pass.
- Old invalid sample: NOT used as evidence; pre-§8.A pasted-body samples and pre-§8.F publisher-URL / bucket-URI samples (including the live-trigger sample `task_id=415ea379ebc6`) all remain invalid; §0.1, §7.2, and §12.3 of the brief / write-up codify the rule.
- Final gate: §8.H PASS; Plan A Matrix Script brief re-corrected YES; product-meaning of `source_script_ref` explicitly stated YES; coordinator action items expanded YES; old invalid samples remain invalid YES; fresh corrected Matrix Script retry sample fully briefed YES; ready for Matrix Script retry sample creation YES; Matrix Script live-run BLOCK released by virtue of §8.H land (subject to the eight conditions in trial brief §12); Plan A Matrix Script trial corrections chain §8.A–§8.H complete; Plan E retains Option F2 as the eventual minting-service resolution path.

### Plan A Trial Correction §8.F — Opaque Ref Discipline (Option F1 Tightening)

- Date: 2026-05-03
- Status: implementation green; ready for signoff
- Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §6 (§8.F — Opaque Ref Discipline vs Operator Usability), §8 (Recommended Ordering — §8.F lands third after §8.G and §8.E), §9 (Gate Recommendation — §8.F BLOCKED on authority decision; Option F1 recommended; F2 / F3 rejected); explicit Chief-Architect decision: Option F1 accepted, Options F2 / F3 rejected; `docs/contracts/matrix_script/task_entry_contract_v1.md` (with §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)" + four new sub-sections landed in this change); `docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md` (§8.E — landed); `docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md` (§8.G — landed); `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (§8.A — landed; the guard whose accepted-scheme set this change tightens); `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (§8.C — landed); `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (§8.B — confirmed); `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` (§8.D — landed)
- Path: Option F1 (tighten the scheme set; defer minting to Plan E; brief operators on the transitional `<token>` convention). Option F2 (in-product minting flow / `POST /assets/mint?kind=script_source` endpoint) and Option F3 (accept the slippage / document only) explicitly REJECTED in this wave per the Chief-Architect decision; Option F2 retained as the Plan E resolution path.
- Execution log: `docs/execution/MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md`
- Code / docs:
  - `gateway/app/services/matrix_script/create_entry.py` (EDIT — `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` tuple shrunk from 8 entries to 4: `("content", "task", "asset", "ref")`; the four dropped schemes are `https`, `http`, `s3`, `gs`; the `_SOURCE_SCRIPT_REF_URI_PATTERN` regex regenerates automatically from the tuple; inline docstring updated to explain the §8.F tightening reasoning; existing whitespace / single-line / max-length / scheme-not-recognised / bare-token / required-field branches all stand verbatim; the four retained schemes are opaque-by-construction inside the product)
  - `gateway/app/templates/matrix_script_new.html` (EDIT — operator-facing HTML `pattern` regex tightened to `^(?:(?:content|task|asset|ref)://\S+|[A-Za-z0-9][A-Za-z0-9._\-:/]{3,})$`; placeholder updated to `content://matrix-script/source/<your-token>`; helper text rewritten to name the four accepted schemes, explicitly reject external web schemes (`https://` / `http://`) and bucket schemes (`s3://` / `gs://`) with "不接受", retain the no-body-paste rule, and add a second hint paragraph documenting the transitional `content://matrix-script/source/<token>` convention with explicit statement that `<token>` is operator-chosen and treated as fully opaque by the product)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (EDIT — §"Source script ref shape (addendum, 2026-05-02)" header renamed to `(addendum, 2026-05-02; tightened by §8.F on 2026-05-03)`; closed scheme set in body updated from 8 to 4 entries; four new additive sub-sections appended: §"Opaque-by-construction discipline (§8.F tightening, 2026-05-03)" — names the four dropped schemes, names the live trigger case, explains the contract-intent reasoning; §"Operator transitional convention (Plan A trial wave only)" — pins `content://matrix-script/source/<token>` as the canonical operator-facing form, declares it operator-discipline-only, pins forward-compatibility for Plan E; §"Why this is contract-tightening AND a usability adjustment"; §"Out of scope for §8.F" — enumerates F2 / F3 as out-of-wave; the §"Phase B deterministic authoring (addendum, 2026-05-03)" sub-tree is unchanged; the closed entry-field set, line-truth/operator-hint rule, deferral table, and forbidden-field list are unchanged)
  - `gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py` (EDIT — module docstring expanded to cite both §8.A and §8.F authority chains; 5 new test cases added: `test_section_f_dropped_schemes_are_now_rejected[https://news.qq.com/...|https://docs.internal.../001|http://legacy.../12|s3://bucket/...|gs://bucket/...]` parametrized rejection check covering all four dropped scheme families plus the live-trigger publisher URL; `test_section_f_accepted_scheme_set_is_exactly_four_opaque_schemes` constant-tuple-shape assertion; `test_section_f_transitional_convention_passes_guard` positive case for `content://matrix-script/source/op-token-001`; `test_template_pattern_is_tightened_to_section_f_scheme_set` HTML-pattern assertion; `test_template_helper_text_documents_transitional_convention` helper-text scheme-list + transitional-convention assertion; existing `test_contract_shaped_refs_are_accepted` parametrize list pruned to drop the four dropped-scheme entries — the seven retained refs are unchanged; existing `test_accepted_scheme_set_is_complete` docstring updated only — the round-trip mechanism is unchanged and now covers four schemes; existing `test_template_replaces_textarea_with_pattern_constrained_input` placeholder assertion adjusted to be prefix-only since the placeholder now ends in `<your-token>`)
  - `docs/execution/MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - opaque-ref discipline restored: the §8.A pragmatic allowance for `https` / `http` (and the parallel allowance for `s3` / `gs`) is removed; the four retained schemes are opaque-by-construction inside the product;
  - the live-trigger publisher URL from the follow-up review §3 (`https://news.qq.com/rain/a/...`) is now rejected at the entry-form HTTP boundary with the same `"scheme is not recognised"` error branch §8.A used for foreign schemes;
  - operator transitional convention pinned: `content://matrix-script/source/<token>` is the canonical operator-facing form for the Plan A trial wave; the product treats `<token>` as fully opaque (never dereferences, never validates uniqueness, never reads back content); operators maintain their own mapping between `<token>` and the source location (private doc, internal page, working notes, etc.);
  - contract-intent restoration documented at the addendum surface: the §8.F tightening sub-section names the dropped schemes and explains the contract intent for each scheme family (external web vs object-storage bucket vs product-internal opaque ref);
  - forward-compatibility statement for Plan E: when Plan E adds the Option F2 in-product minting flow, the transitional convention is replaced by the minted handle without requiring operators to migrate existing handles (the product never bound any meaning to `<token>` beyond opaqueness);
  - regression coverage extended: 5 new test cases close the gap between the §8.A initial guard's accepted set and the §8.F-tightened set, plus assert the operator-facing pattern + helper text mirror the server-side guard.
- What this correction does NOT add:
  - no in-product minting / lookup service (Option F2 explicitly rejected in this wave; retained as Plan E resolution);
  - no asset-library service expansion (Plan C C1, gated to Plan E);
  - no `POST /assets/mint?kind=script_source` endpoint;
  - no §8.D operator brief refresh — §8.H is the natural successor that re-aligns `OPERATIONS_TRIAL_READINESS_PLAN_v1.md` §0.1 / §3.2 / §6.2 / §7.1 in one pass;
  - no `body_ref` template change — the §8.C planner's `content://matrix-script/{task_id}/slot/{slot_id}` is unchanged and remains opaque-by-construction;
  - no Plan B B4 (`result_packet_binding`) artifact-lookup contract change — with URL-shaped refs no longer accepted, Plan E retains full freedom to define artifact-lookup behavior for the four opaque schemes;
  - no widening of the closed scheme set (a future widening requires a contract re-version, not an addendum);
  - no router edit — `tasks.py` is not touched;
  - no schema / sample / packet re-version;
  - no provider / model / vendor / engine controls;
  - no Hot Follow / Digital Anchor scope reopening;
  - no Runtime Assembly / Capability Expansion entry;
  - no second production line onboarding;
  - no §8.A guard mechanism change — only the accepted-scheme tuple shrinks;
  - no §8.B / §8.C / §8.D / §8.E / §8.G reopening;
  - no backwards-compatibility shim for tasks created under the pre-§8.F scheme set (no live evidence relies on the removed schemes; the §8.A addendum's narrowing-permitted clause is satisfied);
  - no CSS-only operator hint — the transitional convention lives in the helper text body, asserted by the regression test;
  - no Plan E gated items (B4, D1, D2, D3, D4) implementation;
  - no Matrix Script live-run unblock — per the user instruction, live-run remains BLOCKED until §8.H operator brief re-correction completes the chain.
- Validation: 28/28 §8.A + §8.F shape-guard cases pass (23 prior §8.A + 5 new §8.F); 200/200 cases pass across §8.A + §8.F (now 28) + §8.B's 4 + §8.C's planner-unit 27 + §8.C end-to-end (13 = 11 prior + §8.G + §8.E) + `test_workbench_variation_phase_b` + operator-visible-surface contracts + guardrails. Live HTTP boundary evidence: `https://news.qq.com/rain/a/20260502A05LYM00` → HTTP 400 with `"scheme is not recognised"`; `s3://bucket/source/001.json` → HTTP 400; `content://matrix-script/source/op-token-001` → HTTP 303 with persisted `source_url` and `config.entry.source_script_ref` exactly equal to the operator-supplied opaque handle.
- Old invalid sample: NOT used as evidence; the prior pre-§8.A sample remains invalid; the pre-§8.F live-trigger sample (`task_id=415ea379ebc6`) which submitted a publisher URL is also invalid (the §8.F guard would reject it); §8.F's evidence is captured live on a fresh post-§8.A / §8.B / §8.C / §8.D / §8.E / §8.G sample with the transitional convention.
- Final gate: §8.F PASS; Option F1 only (F2 / F3 rejected) YES; live publisher URL rejected YES; transitional convention accepted YES; §8.A / §8.B / §8.C / §8.D / §8.E / §8.G not retracted (additive only); ready for §8.H YES; Matrix Script live-run still BLOCKED until §8.H completes; Plan E retains Option F2 as the eventual minting-service resolution path.

### Plan A Trial Correction §8.E — Workbench Shell Suppression (Pure Shell-Suppression Execution Step)

- Date: 2026-05-03
- Status: implementation green; ready for signoff
- Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §5 (§8.E — Workbench Shell Suppression), §8 (Recommended Ordering — §8.E lands second after §8.G), §9 (Gate Recommendation — §8.E READY); `docs/contracts/workbench_panel_dispatch_contract_v1.md` (with §"Shared shell neutrality (addendum, 2026-05-03)" landed in this change); `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (frozen Phase B projection contract — unchanged); `docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md` (§8.G — landed); `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (§8.C — landed); `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (§8.B — confirmed); `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (§8.A — landed); `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` (§8.D — landed)
- Execution log: `docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md`
- Code / docs:
  - `gateway/app/templates/task_workbench.html` (EDIT — four whitelist `{% if task.kind == "hot_follow" %}` gates added around the Hot Follow-only template regions: (1) subtitle-track meta row + pipeline summary meta-item, (2) Deliverables panel + Scenes section panel, (3) Publish hub + Steps + Debug logs panels, (4) inline Hot Follow JS state machine; the i18n runtime `<script src="/static/js/i18n_v185.js">` is left ungated as a global runtime; the `{% set pipeline = ... %}` declarations are left ungated for harmlessness; the matrix_script panel block at lines 257-445 is unchanged and still renders correctly with §8.G's axes-table fix)
  - `docs/contracts/workbench_panel_dispatch_contract_v1.md` (EDIT — additive §"Shared shell neutrality (addendum, 2026-05-03)" appended: declares the shared shell line-neutral; line-specific stage controls render only inside the matched panel block; per-line templates `hot_follow_workbench.html` and `task_workbench_apollo_avatar.html` are unaffected; capability flags deferred; closed dispatch map / `panel_kind` enum / `ref_id` set / closed-by-default rule / resolver shape / forbidden list all stand verbatim)
  - `gateway/app/services/tests/test_matrix_script_phase_b_authoring.py` (EDIT — new 14th case `test_matrix_script_workbench_does_not_render_hot_follow_shell_controls`: POSTs a fresh contract-clean Matrix Script sample, GETs the workbench, strips `<script>` blocks before assertion (so the inlined global `window.__I18N__` translation payload does not mask the visible-shell test), asserts a closed list of 28 forbidden Hot Follow control tokens — pipeline summary `whisper+gemini`/`auto-fallback`, stage DOM ids `id="btn-parse"`/`id="btn-dub"`/`id="btn-pack"`/`id="btn-subtitles"`/`id="btn-scenes"`/`id="hard-subtitles-toggle"`/`id="voice-id"`/`id="dub-provider"`/`id="parse-status"`/`id="dub-status"`/`id="pack-status"`/`id="subs-status"`/`id="audio-preview"`/`id="debug-panel"`, Burmese deliverables `mm.srt`/`mm.txt`/`origin.srt`/`mm_audio`/`/v1/tasks/`, and Hot Follow i18n labels `workbench.deliverables`/`workbench.scenes_section`/`workbench.publish_hub`/`workbench.steps`/`workbench.step.parse`/`workbench.step.dub`/`workbench.step.pack`/`workbench.step.subtitles`/`workbench.meta.subtitle_track`/`workbench.meta.pipeline`/`workbench.logs` — are absent in the visible HTML; positively anchors the matrix_script panel mount markers `data-role="matrix-script-variation-panel"` and `data-panel-kind="matrix_script"` so the negative assertions cannot pass on an empty render)
  - `docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - shared workbench shell now suppresses Hot Follow stage cards / pipeline summary / Burmese deliverable strip / dub-engine selectors / subtitle-track meta row / publish-hub CTA / debug-logs panel / Hot Follow JS state machine on `kind != "hot_follow"`; the operator-visible result on `GET /tasks/{task_id}?created=matrix_script` is now "the shared shell + the Matrix Script Phase B variation panel" with no Hot Follow controls bleeding through (the original mixed-shell defect documented in follow-up review §3 / `task_id=415ea379ebc6` is resolved);
  - additive contract clarification on `workbench_panel_dispatch_contract_v1` declaring shell-shell neutrality, so the next line onboarding (Digital Anchor at Plan E) inherits the same gating discipline without ambiguity;
  - end-to-end regression test that asserts a closed token list of Hot Follow controls is absent in the visible HTML on a fresh matrix_script sample, scoped to the visible HTML region (script blocks stripped) so the global i18n translation payload does not mask the test;
  - shared-shell architecture preserved: per-panel mount inside a shared shell remains the correct design per `workbench_panel_dispatch_contract_v1`; no per-line workbench template introduced for matrix_script.
- What this correction does NOT add:
  - no `workbench_registry.py` change — the `default → task_workbench.html` mapping is unchanged;
  - no per-line workbench template files for `matrix_script` / `digital_anchor`;
  - no capability flags (`shell_capabilities.has_dub_flow`, etc.) — the whitelist form `kind == "hot_follow"` is the simpler, lower-risk implementation per review §5;
  - no change to `hot_follow_workbench.html` or `task_workbench_apollo_avatar.html`;
  - no §8.F scheme tightening — `https`/`http` remain in the §8.A accepted-scheme set; opaque-ref discipline tightening scoped to §8.F follow-up (BLOCKED on authority decision);
  - no §8.D operator brief re-correction — §8.H is the natural successor once §8.E / §8.F / §8.G all land;
  - no Phase B planner / projector / router / wire-up change;
  - no schema / sample / packet re-version;
  - no `PANEL_REF_DISPATCH` widening; no §8.B dispatch logic change;
  - no §8.G axes-table change — the Jinja item-access fix lives inside the matrix_script panel block and is unaffected by §8.E gating;
  - no provider / model / vendor / engine controls;
  - no Hot Follow / Digital Anchor scope reopening;
  - no Runtime Assembly / Capability Expansion entry;
  - no second production line onboarding;
  - no Asset Library / promote (Plan C C1–C3) work;
  - no Plan E gated items (B4, D1, D2, D3, D4) implementation;
  - no CSS-only suppression — review §9 hard red line is observed: suppression is in the Jinja render path, asserted by the regression test;
  - no panel-readability re-check — that was §8.G's concern; §8.E is shell-suppression only.
- Validation: 13/13 §8.C end-to-end suite cases pass after the §8.E gates and new test (11 §8.C prior + §8.G axes-table + §8.E suppression); 195/195 cases pass across §8.A's 23, §8.B's 4, §8.C's planner-unit 27 + end-to-end (now 13), `test_workbench_variation_phase_b`, the operator-visible-surface contracts, and guardrails. 166/166 workbench-keyword tests pass (Hot Follow per-line workbench unaffected; Apollo Avatar workbench unaffected). Live render evidence on a fresh contract-clean sample (`task_id=2df7c79311a6`, `variation_target_count=4`, `target_language=mm`, `source_script_ref=content://matrix-script/source/8e-evidence-001`) confirms: matrix_script panel mount + §8.G axes table all PRESENT in visible HTML; all 21 closed-list Hot Follow tokens (pipeline summary, stage DOM ids, Burmese deliverables, Hot Follow i18n labels) all ABSENT in visible HTML. Pre-existing environment limitation `test_op_download_proxy_uses_attachment_redirect_for_final_video` recorded in §8.A / §8.B / §8.C / §8.G logs is unaffected (template + test edit only).
- Old invalid sample: NOT used as evidence; the prior pre-§8.A sample remains invalid; §8.E's evidence is on a fresh post-§8.A / §8.B / §8.C / §8.D / §8.G sample.
- Final gate: §8.E PASS; Hot Follow controls suppressed on matrix_script YES; matrix_script panel mount preserved YES; Hot Follow per-line workbench unaffected YES; Apollo Avatar per-line workbench unaffected YES; ready for §8.F YES (with §8.F still BLOCKED on Options F1/F2/F3 authority decision); §8.A / §8.B / §8.C / §8.D / §8.G not retracted (additive only); ops trial retry remains BLOCKED until §8.F also lands per the follow-up review §9 ordering.

### Plan A Trial Correction §8.G — Phase B Panel Render Correctness (Narrow Template Fix)

- Date: 2026-05-03
- Status: implementation green; ready for signoff
- Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §7 (§8.G — Phase B Panel Render Correctness), §9 (Gate Recommendation — §8.G READY, land first); `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (frozen Phase B projection contract — unchanged); `docs/contracts/matrix_script/variation_matrix_contract_v1.md` (axes shape — unchanged); `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (§8.C — landed; planner output that this template renders); `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (§8.B — confirmed); `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (§8.A — landed); `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` (§8.D — landed)
- Execution log: `docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md`
- Code / docs:
  - `gateway/app/templates/task_workbench.html` (EDIT — Jinja item-access fix in the Axes-table values cell inside the `panel_kind="matrix_script"` mount: hoist `{% set axis_values = axis["values"] %}`, replace every `axis.values…` with `axis_values…` so `is mapping` / `is iterable and not string` resolve against the actual list/dict instead of the dict's bound `values()` method; net 8 lines of edits, line count unchanged at 658)
  - `gateway/app/services/tests/test_matrix_script_phase_b_authoring.py` (EDIT — new 12th case `test_axes_table_renders_human_readable_values` scoped to the axes-table HTML region between `<h3>Axes</h3>` and `<h3>Cells × Slots</h3>` so cell-level `axis_selections` cannot mask a broken row render; asserts tone values `formal`/`casual`/`playful`, audience values `b2b`/`b2c`/`internal`, and length range `min=30 · max=120 · step=15` all render inside the region; asserts the broken bound-method repr `<built-in method values` is absent inside the region and absent in the body; defensive `<built-in method values` negative also added to the existing `test_get_workbench_renders_real_axes_cells_slots` so any future regression of the same shape is caught by both tests; imports `LENGTH_RANGE` from the planner)
  - `docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - Jinja attribute-vs-item access collision fixed at the template
    level: `axis.values` previously resolved to the dict's bound
    `values()` method (a callable that is neither `mapping` nor
    `iterable`), so every axes row fell through the `else` branch and
    rendered the bound-method repr `<built-in method values of dict
    object at 0x…>` for `tone`, `audience`, and `length`. The fix
    uses item access (`axis["values"]`) which returns the actual list
    (categorical / enum) or dict (range), so the `is mapping` /
    `is iterable and not string` branches resolve correctly: tone and
    audience render their values joined by ` · `; length renders
    `min=… · max=… · step=…` from the dict's keys.
  - Axes-table-scoped regression test that closes the §8.C test escape
    documented in the follow-up blocker review §4.3 (the prior §8.C
    `test_get_workbench_renders_real_axes_cells_slots` only asserted
    presence of tone/audience tokens *somewhere* in the body, which
    passed because cell-level `axis_selections` like `tone=formal`
    surface those tokens elsewhere on the page even when the axes table
    itself is broken).
- What this correction does NOT add:
  - no contract change — no edits to `docs/contracts/matrix_script/**`
    (including the §8.A and §8.C addenda on `task_entry_contract_v1`,
    the `workbench_variation_surface_contract_v1`, the
    `variation_matrix_contract_v1`, the `slot_pack_contract_v1`, and
    `packet_v1`);
  - no schema / sample / packet re-version;
  - no Phase B planner change — `phase_b_authoring.py` is consumed
    read-only;
  - no projector change — `workbench_variation_surface.py` is consumed
    read-only;
  - no router change — `tasks.py` is not touched;
  - no `PANEL_REF_DISPATCH` widening; no §8.B dispatch logic change;
  - no §8.E shell-suppression change — Hot Follow stage cards /
    pipeline summary / dub-engine selectors / Burmese deliverable rows
    intentionally still rendered by the shared shell on
    `kind=matrix_script` tasks; that operator-blocking shell defect
    remains scoped to §8.E follow-up;
  - no §8.F scheme tightening — `https`/`http` remain in the §8.A
    accepted-scheme set; opaque-ref discipline tightening scoped to
    §8.F follow-up;
  - no §8.D operator brief re-correction — §8.H is the natural
    successor once §8.E / §8.F / §8.G all land;
  - no provider / model / vendor / engine controls;
  - no Hot Follow / Digital Anchor scope reopening;
  - no Runtime Assembly / Capability Expansion entry;
  - no second production line onboarding;
  - no Asset Library / promote (Plan C C1–C3) work;
  - no Plan E gated items (B4, D1, D2, D3, D4) implementation;
  - no template gating predicate (`task.kind == "hot_follow"`) — that
    is §8.E's correction;
  - no audit of `task_workbench.html` Hot Follow regions (§8.G's audit
    is scoped to the matrix_script panel's own dict-method-collision
    patterns; the only other `.values` / `.keys` / `.items` /
    `.update` occurrences in the template are explicit method *calls*,
    which work correctly).
- Validation: 12/12 §8.C end-to-end suite cases pass after the §8.G
  fix (11 prior + 1 new `test_axes_table_renders_human_readable_values`,
  with the existing `test_get_workbench_renders_real_axes_cells_slots`
  also tightened to assert `<built-in method values` is absent);
  194/194 cases pass across §8.A's 23, §8.B's 4, §8.C's planner-unit
  27 and end-to-end (now 12), `test_workbench_variation_phase_b`,
  operator-visible-surface contracts, and guardrails. Live render
  evidence on a fresh contract-clean sample (`task_id=6640deeeb1a6`,
  `variation_target_count=4`, `target_language=mm`,
  `source_script_ref=content://matrix-script/source/8g-evidence-001`)
  confirms the axes-table region renders `formal · casual · playful`
  for tone, `b2b · b2c · internal` for audience, `min=30 · max=120 ·
  step=15` for length, and `<built-in method values` is absent in the
  body. Pre-existing environment limitation
  (`test_op_download_proxy_uses_attachment_redirect_for_final_video`)
  recorded in §8.A / §8.B / §8.C logs is unaffected by §8.G (template
  edit only).
- Old invalid sample: NOT used as evidence; the prior pre-§8.A sample
  remains invalid per the original blocker review §9 and the follow-up
  review §1, §4.3, §9; §8.G's evidence is on a fresh post-§8.A /
  §8.B / §8.C / §8.D sample.
- Final gate: §8.G PASS; axes table readable YES; ready for §8.E YES;
  §8.A / §8.B / §8.C / §8.D not retracted (additive only); ops trial
  retry remains BLOCKED until §8.E and §8.F also land per the
  follow-up review §9 ordering.

### Plan A Trial Correction §8.D — Operator Brief Correction (Documentation-only)

- Date: 2026-05-03
- Status: documentation correction green; ready for signoff
- Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.D; `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (operator-facing trial brief — corrected by this change); `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` (trial coordination write-up — extended by an §11 §8.D addendum); `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (§8.A — landed); `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (§8.B — confirmed); `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (§8.C — landed)
- Execution log: `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md`
- Doc changes:
  - `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (UPDATED — added §0.1 binding "Matrix Script Trial Sample Validity (post-§8.A / §8.B / §8.C)" rule; refreshed authority list with §8.A / §8.B / §8.C / §8.D execution logs and the trial blocker review; corrected §3.1 Matrix Script row, §3.2 create-entry / Workbench / Delivery rows, §3.3 inspect-only list, §5.2 Workbench explanation 口径 with empty-fallback coordinator note, §6.2 Matrix Script line-by-line guidance, §7.1 first-wave samples, §7.2 samples-to-avoid; expanded §8 risk list with five new Matrix Script-specific rows; added §11.1 trial-corrections landed-history block; corrected §12 Final Readiness Conclusion with §8.A / §8.B / §8.C / §8.D PASS rows and condition #6 binding samples to §0.1)
  - `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` (UPDATED — refreshed front-matter date / status / authority list; appended §11 "Matrix Script Plan A Trial Corrections — Addendum (2026-05-03)" with §11.1 why-original-was-invalid, §11.2 trial-corrections landed-status table, §11.3 static-pass overlay for Matrix Script rows, §11.4 coordinator action items, §11.5 final corrected coordinator judgment)
  - `docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - operator-facing documentation now reflects the accepted §8.A / §8.B / §8.C results: old broken sample remains invalid evidence; fresh corrected sample must be post-§8.A contract-clean, must use the formal `/tasks/matrix-script/new` POST, has real Phase B truth (axes / cells / slots) per §8.C, mounts the Matrix Script Phase B variation panel per §8.B; Matrix Script workbench is now inspectable for real packet truth
  - explicit valid vs invalid Matrix Script trial sample criteria pinned in the operator brief §0.1
  - explicit risk-list coverage for old-sample reuse, body-text paste, empty-fallback observation, deterministic-axes misreport, legacy-path submission, and panel-authoring expectation
  - inspect-only / contract-only boundaries preserved verbatim: Matrix Script Delivery Center stays inspect-only with `not_implemented_phase_c` placeholder rows by Plan A §3.2 and Plan B B4; Matrix Script Phase D.1 publish-feedback closure surface stays as already shipped per `publish_feedback_closure_contract_v1`
- What this correction does NOT add:
  - no runtime behavior change — no `.py`, no `.html`, no schema, no sample, no contract, no template, no test edits
  - no contract change — no edits to any `docs/contracts/**` file (including the §8.A and §8.C addenda already on `task_entry_contract_v1`)
  - no `PANEL_REF_DISPATCH` widening; no schema / sample / packet re-version
  - no §8.A / §8.B / §8.C reopening; no workbench redesign
  - no Hot Follow / Digital Anchor scope reopening; no Runtime Assembly / Capability Expansion entry
  - no provider / model / vendor / engine controls
  - no Plan E gated items (B4, D1, D2, D3, D4, Digital Anchor B1 / B2 / B3 implementation)
  - no second production line onboarding; no Asset Library / promote (Plan C C1–C3) work
  - no live-trial execution (operations team appends live-run results to `PLAN_A_OPS_TRIAL_WRITEUP_v1.md` §8 separately)
- Validation: documentation-only change; per `ENGINEERING_RULES.md` §10 there is no runtime regression to run; the §8.A / §8.B / §8.C suites remain green on baseline `9f25b89` and are not affected (no code edited); cross-checks recorded in §4.2 of the §8.D execution log confirm the brief consumes §8.A's accepted scheme set verbatim, §8.B's captured render markers verbatim, §8.C's deterministic axes / cells / slots / `body_ref` template verbatim, the Plan B B4 inspect-only Delivery Center boundary, and the Phase D.1 closure surface boundary.
- Old invalid sample: NOT used as evidence; the prior sample remains invalid per the blocker review §9 and §8.A's PASS gate; §8.D codifies this rule in the operator brief §0.1, §6.2, §7.2, §8.
- Final gate: §8.D PASS; Plan A Matrix Script brief corrected YES; old invalid sample remains invalid YES; fresh corrected Matrix Script retry sample fully briefed YES; ready for Matrix Script retry sample creation YES.

### Plan A Trial Correction §8.C — Phase B Truth Population (Deterministic Authoring)

- Date: 2026-05-03
- Status: implementation green; ready for signoff
- Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.C; `docs/contracts/matrix_script/task_entry_contract_v1.md` (with §"Phase B deterministic authoring (addendum, 2026-05-03)" landed in this change); `docs/contracts/matrix_script/variation_matrix_contract_v1.md`; `docs/contracts/matrix_script/slot_pack_contract_v1.md`; `docs/contracts/matrix_script/packet_v1.md`; `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- Execution log: `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md`
- Path: Option C1 (minimal real Phase B authoring). Option C2 (fixture-LS-delta policy) explicitly rejected — wave authority does not require a stub, and the entry contract's existing Mapping note (entry → packet) had already pre-specified the C1 mapping.
- Code / docs:
  - `gateway/app/services/matrix_script/phase_b_authoring.py` (NEW — pure deterministic planner exporting `derive_phase_b_deltas(entry, task_id) -> tuple[dict, dict]`; canonical axes `tone`/`audience`/`length`; index-aligned 1-to-1 cell↔slot pairing; opaque `body_ref` template `content://matrix-script/{task_id}/slot/{slot_id}`; no IO, no clock, no randomness)
  - `gateway/app/services/matrix_script/create_entry.py` (UPDATED — `from copy import deepcopy`; import `derive_phase_b_deltas`; call once inside `build_matrix_script_task_payload`; populate `delta` on both LS1 and LS2 in the packet mirror and the top-level mirror)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (UPDATED — appended §"Phase B deterministic authoring (addendum, 2026-05-03)" pinning the canonical axes, kind sets, pairing rule, body_ref template, determinism statement, and Plan E removal path)
  - `tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py` (NEW — 27-case planner unit + contract conformance suite: axes pinned, kind sets closed, cardinality matches `variation_target_count` for k ∈ {1, 2, 4, 9, 12}, round-trip resolution at k ∈ {1, 4, 12}, axis-selection drawn from declared values, all 12 cells distinct at k=12, opaque body_ref shape, slot defaults, language scope, no forbidden state/vendor/donor field, deterministic output, no entry mutation, no aliasing across calls, projector consumes authored delta verbatim)
  - `gateway/app/services/tests/test_matrix_script_phase_b_authoring.py` (NEW — 11-case end-to-end HTTP-boundary suite: POST persists populated deltas on both mirrors; round-trip resolves through persisted packet; projector consumes authored delta; rendered HTML carries cell/slot ids, axis ids, value tokens; empty-fallback messages absent; cardinality at k=1 and k=12; slot language_scope carries entry's `mm`/`vi`; §8.A guard regression; §8.B dispatch regression; render context attaches variation surface)
  - `docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - Synchronous deterministic Phase B authoring step at task-creation time. Given a valid `MatrixScriptCreateEntry` and the create-entry-assigned `task_id`, the planner emits populated `variation_matrix.delta` (`axis_kind_set` + 3 canonical axes + `variation_target_count` cells) and `slot_pack.delta` (`slot_kind_set` + per-cell slots).
  - Round-trip integrity by construction: `cells[i].script_slot_ref == slots[i].slot_id` and `slots[i].binds_cell_id == cells[i].cell_id` for every `i ∈ [0, variation_target_count)`. 1-to-1 pairing also satisfies `slot_pack_contract_v1` §"Cross-binding rules" "A slot MAY be referenced by at most one cell".
  - Body refs stay opaque per `slot_pack_contract_v1` §"Forbidden": `body_ref = "content://matrix-script/{task_id}/slot/{slot_id}"` derives from `task_id` and `slot_id` only — never embeds body text, never piggybacks on the operator-supplied `source_script_ref`.
  - Contract addendum on `task_entry_contract_v1.md` pins the canonical axes (`tone` categorical, `audience` enum, `length` range with `{min: 30, max: 120, step: 15}`), kind sets, pairing rule, body_ref template, determinism statement, and explicit Plan E removal path. The addendum is additive: the closed entry-field set, mapping note, line-truth/operator-hint rule, deferral table, and §8.A source-ref-shape addendum are unchanged.
- What this correction does NOT add:
  - no Phase B authoring surface in the workbench (Phase B render remains read-only per `workbench_variation_surface_contract_v1`);
  - no operator brief correction (§8.D);
  - no Phase D publish-feedback closure write-back (still contract-only via Plan B B3);
  - no Phase C delivery binding work (Matrix Script Delivery Center remains inspect-only with `not_implemented_phase_c` placeholders);
  - no schema / sample / packet re-version;
  - no template / projector / router change;
  - no widening of `PANEL_REF_DISPATCH`;
  - no `g_lang` token alphabet pinning;
  - no consumption of optional entry hints (`audience_hint`, `tone_hint`, `length_hint`) — addendum names this as permitted Plan E future work;
  - no Hot Follow / Digital Anchor / Runtime Assembly / Capability Expansion entry;
  - no provider / model / vendor / engine controls;
  - no Plan E gated items (B4 result_packet_binding, D1 publish_readiness, D2 final_provenance, D3 panel-dispatch-as-contract-object, D4 advisory producer);
  - no second production line onboarding;
  - no Asset Library / promote (Plan C C1–C3) work.
- Validation: 27/27 planner unit + contract conformance cases pass; 11/11 end-to-end HTTP-boundary cases pass; 193/193 cases pass across §8.A + §8.B + §8.C + matrix_script contracts + operator-visible-surface contracts + guardrails. Pre-existing environment limitation (`test_op_download_proxy_uses_attachment_redirect_for_final_video`) reproduces on baseline `970b4dc` without §8.C edits — confirmed unrelated.
- Live render evidence: fresh contract-clean Matrix Script sample (`task_id=b224f07d2c5a`, `variation_target_count=4`, `target_language=mm`) renders `cell_001..cell_004`, `slot_001..slot_004`, canonical axis ids `tone`/`audience`/`length`, and tone/audience value tokens in the rendered HTML. Empty-fallback messages (`"No axes resolved on this packet"`, `"No cells resolved on this packet"`, `"No slots resolved on this packet"`) absent.
- Old invalid sample: NOT used as evidence; the prior sample remains invalid per the blocker review §9.
- Final gate: §8.C PASS; fresh corrected Matrix Script sample possible YES; Phase B truth populated YES; cells↔slots round-trip resolves YES; mounted variation surface renders real inspectable data YES; packet truth aligned to frozen contracts YES; old invalid sample reusable NO; ready for Matrix Script retry sample creation YES.

### Plan A Trial Correction §8.B — Workbench Panel Dispatch Confirmation

- Date: 2026-05-03
- Status: confirmation green; no narrow fix required
- Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.B; `docs/contracts/workbench_panel_dispatch_contract_v1.md`; `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- Execution log: `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md`
- Code / docs:
  - `gateway/app/services/tests/test_matrix_script_workbench_dispatch.py` (NEW — 4-case end-to-end suite using a fresh, contract-clean post-§8.A sample; asserts redirect target, persisted dispatch inputs, resolver `panel_kind`, and rendered Phase B variation panel markup)
  - `docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` (NEW — this row)
- What this confirmation proves:
  - GET `/tasks/{task_id}` for `kind=matrix_script` lands on `task_workbench.html` (the shared shell). Per-line dispatch is via `panel_kind` mounting inside the shared shell, not via per-line template files (per `workbench_panel_dispatch_contract_v1`, which pins `(ref_id → panel_kind)` only).
  - `resolve_line_specific_panel(packet)` returns `panel_kind="matrix_script"` and surfaces both `matrix_script_variation_matrix` and `matrix_script_slot_pack` for a fresh contract-clean sample.
  - `wiring.py` attaches the formal `matrix_script_workbench_variation_surface_v1` projection when the panel mounts as `matrix_script`.
  - The rendered HTML contains `data-role="matrix-script-variation-panel"`, `data-panel-kind="matrix_script"`, the projection name, both ref_ids, and the operator-visible "Matrix Script — Variation Panel" heading; the empty-slot fallback message is absent.
  - The blocker-review row #2 ("Workbench is still the generic engineering shell") is dispatch-correct on contract-clean samples; the prior operator observation conflated upstream contamination (§8.A's pasted body text) and empty LS deltas (§8.C's authoring gap) with a dispatch defect.
- What this confirmation does NOT add:
  - no per-line workbench template (dispatch remains panel-mount inside the shared shell);
  - no widening of `PANEL_REF_DISPATCH`;
  - no Phase B authoring capability (§8.C remains the binding precondition for *populated* axes / cells / slots);
  - no operator brief correction (§8.D);
  - no Hot Follow / Digital Anchor change;
  - no provider / model / vendor / engine controls;
  - no packet / schema / sample re-version.
- Old invalid sample: NOT used as evidence; the prior sample remains invalid per the blocker review §9.
- Final gate: §8.B PASS; workbench route confirmed YES; Phase B variation surface mounted YES; ready for §8.C YES.

### Plan A Trial Correction §8.A — Source Script Ref Shape Guard

- Date: 2026-05-02
- Status: implementation green; ready for signoff
- Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.A
- Execution log: `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md`
- Code / docs:
  - `gateway/app/services/matrix_script/create_entry.py` (UPDATED — `_validate_source_script_ref_shape`, `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES`, `SOURCE_SCRIPT_REF_MAX_LENGTH`)
  - `gateway/app/templates/matrix_script_new.html` (UPDATED — `<textarea>` replaced with `<input type="text">` constrained by `pattern` and `maxlength`; helper text forbids body paste)
  - `docs/contracts/matrix_script/task_entry_contract_v1.md` (UPDATED — §"Source script ref shape (addendum, 2026-05-02)" pinning the closed scheme set)
  - `gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py` (NEW — 23-case suite: rejection branches, accepted shapes, payload-builder regression, HTTP boundary, template wiring)
  - `docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` (NEW — this row)
- What this correction adds:
  - Server-side ref-shape guard for `source_script_ref` running before `build_matrix_script_task_payload`. Closed accepted shapes: URI with closed scheme (`content`, `task`, `asset`, `ref`, `s3`, `gs`, `https`, `http`) or bare token id (`^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$`). Envelope: single line, no whitespace, ≤512 chars.
  - Operator-facing input shape mirrors the server guard via `pattern` and `maxlength`; helper text explicitly forbids pasting body text.
  - Contract addendum pins the closed scheme set as exhaustive at v1.
- What this correction does NOT add:
  - no Phase B authoring capability (§8.C remains the binding precondition for trial evidence);
  - no panel-dispatch route trace (§8.B);
  - no operator brief correction (§8.D);
  - no Digital Anchor implementation (Plan B B1 / B2 still gated to Plan E);
  - no Hot Follow change;
  - no provider / model / vendor / engine controls;
  - no packet / schema / sample re-version.
- Final gate: §8.A PASS; current sample reusable NO; ready for §8.B YES.

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
