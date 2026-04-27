# Matrix Script Phase D.1 — Publish Feedback Closure Write-Back Evidence v1

Date: 2026-04-28
Status: implementation green (minimal write-back); awaiting architect + reviewer signoff
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` Phase D
- `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` (Phase D.0 freeze)
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (Phase C boundary)
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (Phase B boundary)
- `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A boundary)
- `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
- `schemas/packets/matrix_script/packet.schema.json`

## Scope

Phase D.1 lands the **minimal** publish feedback closure write-back path
defined by the Phase D.0 contract freeze. The closure surface
`matrix_script_publish_feedback_closure_v1` is now persistable in-process
through an additive-only module that:

1. seeds variation-level rows using the canonical
   `cell_id ↔ variation_id` join from
   `line_specific_refs[matrix_script_variation_matrix].delta.cells[]`;
2. accepts append-only events in `feedback_closure_records[]`;
3. applies last-write-wins per-field updates to `variation_feedback[]`
   under the contract's origin rules
   (operator vs platform vs system);
4. enforces the closed `publish_status` enum, closed event-kind enum,
   closed actor-kind enum, and closed `channel_metrics` snapshot keys.

The Phase C delivery binding projection (`delivery_binding.py`) is
**unchanged**. It continues to expose `phase_d_deferred` and remains a
read-only consumer; it does not own, mutate, or write into closure
truth.

## Files added

- `gateway/app/services/matrix_script/publish_feedback_closure.py`
  — new module hosting the closure shape, validation, append-only
  event application, and an in-process `InMemoryClosureStore`.
- `tests/contracts/matrix_script/test_publish_feedback_closure_phase_d1.py`
  — Phase D.1 validation suite.
- `docs/execution/evidence/matrix_script_phase_d1_publish_feedback_closure_writeback_v1.md`
  — this evidence doc.

## Files updated

- `gateway/app/services/matrix_script/__init__.py`
  — exports the new closure entry points alongside the existing Phase B
  / Phase C projectors. No projector behavior changed.
- `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md`
  — Phase D.1 implementation row added.
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
  — Phase D.1 evidence + tests rows added.
- `tests/contracts/matrix_script/test_task_entry_phase_a.py`
  — phase-sequence assertion updated from “Phase D NOT STARTED” to
  “Phase D.0 contract freeze landed + Phase D.1 implementation row
  present”, matching the new wave reality.

## Boundary assertions

- **Phase A/B/C frozen truth is unchanged.** No edits to packet, schema,
  sample, task entry contract, workbench surface contract, delivery
  binding contract, or Phase C projector code. Phase C projection
  output for the sample packet is byte-identical before and after a
  closure write-back (asserted by
  `test_phase_c_delivery_projection_remains_read_only_after_phase_d_writes`).
- **Closure is its own ownership zone.** It is not a projection of the
  packet and it is not a projection of the Phase C delivery binding.
  It joins to the packet only through `cell_id` and copies `line_id` /
  `packet_version` once at creation per the contract.
- **Append-only audit.** `feedback_closure_records[]` is grown with one
  row per accepted event; existing rows are never edited or removed.
- **Closed enums enforced.** `publish_status`, `event_kind`,
  `actor_kind`, and the `channel_metrics` key set are validated; any
  unknown value raises `ClosureValidationError` and never lands in the
  store.
- **Origin rules enforced.** Operator events may only set
  `publish_status` ∈ {pending, retracted}; platform callbacks may only
  set {published, failed}; `channel_metrics` is only writable through
  `metrics_snapshot`; `operator_publish_notes` is only writable through
  `operator_note`.

## Out of scope (intentionally not done in Phase D.1)

- No durable persistence backend (database, file, queue). The
  `InMemoryClosureStore` is a minimal in-process surface; a future wave
  may swap in durable storage without redesigning the closure shape.
- No HTTP / WebSocket / callback-handler routing. The module exposes a
  pure-Python API; transport binding is a separate later wave.
- No ACL / auth model for closure mutation. Out of Phase D scope per
  the contract.
- No analytics aggregation, dashboards, or cross-line feedback rollup.
- No per-deliverable feedback (Phase D is variation-level only).
- No multi-channel arbitration / routing policy.
- No provider / model / vendor / engine controls.
- No additive schema file under `schemas/feedback/matrix_script/` —
  the contract permits but does not require one at the minimal write-
  back step, and adding it now would precede a real persistence
  format. Deferred to a later persistence wave.
- No Digital Anchor scope, no Hot Follow scope, no W2.2 / W2.3 scope.
- No frontend rebuild, no debug panel mutation.
- No mutation of the Phase C delivery projection or its router.

## Tests run

- `python3 -m pytest tests/contracts/matrix_script/ -q`
  — full Matrix Script contract suite, Phases A/B/C/D.1.

## Acceptance against Phase D.0 contract

| Phase D.0 acceptance item | Phase D.1 status |
|---|---|
| closure truth defined as `matrix_script_publish_feedback_closure_v1` with `variation_feedback[]` and `feedback_closure_records[]` | implemented as the in-process closure shape |
| ownership / mutability per-field origin (operator vs platform vs system) | enforced in `apply_event` |
| boundary vs Phase A/B/C forbids mutation of packet / entry / workbench / delivery / manifest / metadata projection | asserted by tests; no edits to those modules |
| no packet schema / sample change | confirmed |
| no rewriting of A/B/C frozen truth | confirmed |
| evidence / log / index write-back | this doc + log row + index rows |
| reviewable as one isolated wave with no implementation outside the closure module | confirmed |

## Remaining blockers after Matrix Script line closure

1. Durable persistence wave for closures (database / queue / callback
   handler) — not authorized here; gated on Phase D.1 signoff and an
   explicit follow-on brief.
2. Transport surface (HTTP route or worker callback) for operator and
   platform events — gated on the same.
3. Optional additive `schemas/feedback/matrix_script/publish_feedback_closure.schema.json`
   — to be issued once a persistence format is committed.
4. Architect signoff that the Matrix Script first production line
   (Phase A → B → C → D.1) is reviewable as one closed wave before
   Digital Anchor wave start.
