# Matrix Script Publish Feedback Closure Contract v1

Date: 2026-04-28
Status: Phase D.0 contract freeze (Matrix Script First Production Line Wave — Publish Feedback Closure). Implementation is **not** in this wave.
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` Phase D
- `docs/contracts/matrix_script/task_entry_contract_v1.md` (Phase A boundary)
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` (Phase B boundary)
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (Phase C boundary)
- `docs/contracts/matrix_script/packet_v1.md` (frozen packet truth)
- `schemas/packets/matrix_script/packet.schema.json`

## Purpose

Define the formal Publish Feedback Closure for Matrix Script. This contract freezes:

1. the variation-level feedback object;
2. the publish-side fields owned by the closure (URL, status, channel metrics, operator notes);
3. the feedback closure record shape;
4. ownership and mutability rules separating Phase D feedback truth from Phase A/B/C frozen truth;
5. the (additive-only) schema impact, if any;
6. mapping from Phase C delivery projection fields to Phase D feedback fields;
7. what is intentionally outside Phase D.

This contract does **not** authorize, define, or describe write-back implementation. Phase D.0 is a contract freeze only. A separate later wave (Phase D.1+) will be required to implement write-back paths.

## Phase D.0 closure object

The formal Phase D surface is named `matrix_script_publish_feedback_closure_v1`.

It is a new feedback-truth surface, owned by Phase D, distinct from:

- Phase A entry truth (`matrix_script_task_entry_v1`);
- Phase B workbench projection (`matrix_script_workbench_variation_surface_v1`);
- Phase C delivery projection (`matrix_script_delivery_binding_v1`).

It is **not** a projection of the Phase C delivery binding. It is **not** owned by the Matrix Script packet. It is its own ownership zone.

### Top-level sections

| Section | Purpose | Mutability |
|---|---|---|
| `closure_id` | Stable id for one publish-feedback closure record set tied to one packet instance | immutable once created |
| `line_id` | Always `matrix_script` | immutable |
| `packet_version` | Packet version this closure binds to | immutable |
| `variation_feedback[]` | Variation-level feedback rows, one per `cell_id` (variation) | mutable per row by closure owner |
| `feedback_closure_records[]` | Append-only audit trail of closure events | append-only |

### `variation_feedback[]` row

Each row is a per-variation feedback object. The variation join rule is:

`variation_feedback[].variation_id == matrix_script_variation_matrix.delta.cells[].cell_id`

Row fields:

| Field | Source / origin | Owner | Mutability |
|---|---|---|---|
| `variation_id` | packet `cells[].cell_id` (joined, not copied as truth) | closure | set once at row creation |
| `publish_url` | operator action OR platform callback | closure | mutable; last-write-wins per closure event |
| `publish_status` | operator action OR platform callback | closure | enum (see below) |
| `channel_metrics` | platform callback / external metrics provider | closure | mutable; recorded as snapshots |
| `operator_publish_notes` | operator action | closure | mutable free-text, non-truth |
| `last_event_id` | id of the most recent `feedback_closure_records[]` entry | closure | mutable pointer |

`publish_status` is a closed Phase D.0 enum:

```
{ pending, published, failed, retracted }
```

These values are feedback-side states. They are **not** packet-truth state, **not** delivery readiness, and **not** workbench readiness. They must not be projected back into Phase A/B/C.

### `channel_metrics` shape

`channel_metrics` is a structured snapshot, not an open bag:

| Field | Type | Notes |
|---|---|---|
| `channel_id` | string | the publish channel (e.g. an external platform ref); closure-owned |
| `captured_at` | ISO-8601 timestamp | when the snapshot was taken |
| `impressions` | integer ≥ 0 | optional |
| `views` | integer ≥ 0 | optional |
| `engagement_rate` | float in [0, 1] | optional |
| `completion_rate` | float in [0, 1] | optional |
| `raw_payload_ref` | opaque reference | optional pointer to provider raw payload, not embedded |

Phase D.0 does not allow other metric keys. Additional metric kinds require an explicit re-version of this contract.

### `feedback_closure_records[]` row

This is the append-only audit trail. Each row is one closure event:

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | stable id within this closure |
| `variation_id` | string | which variation the event applies to |
| `event_kind` | enum: `{ operator_publish, operator_retract, operator_note, platform_callback, metrics_snapshot }` | |
| `recorded_at` | ISO-8601 timestamp | |
| `actor_kind` | enum: `{ operator, platform, system }` | |
| `payload_ref` | opaque reference | per-event payload pointer, not embedded |

`feedback_closure_records[]` is append-only. Edits and deletes are forbidden. Corrections are recorded as new events.

## Ownership and mutability

| Object | Owner | Mutability | Phase |
|---|---|---|---|
| Matrix Script packet (`packet_v1`) | product (line packet author) | frozen per envelope E4 | A truth |
| Task entry surface | Phase A contract | read at creation only | A |
| Workbench variation surface | Phase B projection | read-only projection | B |
| Delivery binding projection | Phase C projection | read-only projection | C |
| Publish feedback closure | Phase D contract | mutable per rules above | D |

Phase D owns publish feedback closure **only**. Phase D **must not** mutate:

- Matrix Script packet truth (any field under `generic_refs`, `line_specific_refs`, `binding`, `evidence`, `metadata`);
- Phase A entry contract;
- Phase B workbench projection helper or its outputs;
- Phase C delivery projection helper or its outputs;
- `manifest.*` fields (Phase C read-only display);
- `metadata_projection.*` fields (Phase C read-only display);
- `evidence.ready_state` or any other packet readiness field.

Phase D **must not** introduce truth-shape state fields into packet, workbench, or delivery surfaces. The forbidden field list from Phase A/B/C is reasserted: `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`. These remain banned **everywhere outside this Phase D closure**, including inside the Matrix Script packet and inside any Phase C projection.

## Boundary statement

The following boundary is binding for Phase D.0 and for all later Phase D.x implementation waves:

1. **Phase C delivery binding remains read-only.** The delivery projection helper `project_delivery_binding(packet)` and its returned shape (`delivery_pack`, `result_packet_binding`, `manifest`, `metadata_projection`, `phase_d_deferred`) are not modified by Phase D. They remain pure projections of packet truth.
2. **Phase D owns feedback closure only.** All publish-feedback truth (URLs, statuses, metrics, notes, audit events) lives under `matrix_script_publish_feedback_closure_v1`. It is its own ownership zone, not a projection.
3. **Phase D does not rewrite A/B/C packet truth.** The Matrix Script packet, the task entry contract, the workbench surface contract, and the delivery binding contract are frozen and unchanged.
4. **`manifest.*` and `metadata_projection.*` remain display-only.** Phase D may read them; Phase D must not write into them and must not make them carry feedback truth.
5. **Forbidden truth-shape state fields remain banned** in packet, entry, workbench, and delivery surfaces. The Phase D `publish_status` enum is feedback-side state and lives only inside `variation_feedback[]`; it must not be hoisted into packet or any Phase A/B/C surface.

## Schema impact

Phase D.0 makes **no changes** to:

- `schemas/packets/matrix_script/packet.schema.json`
- `schemas/packets/matrix_script/sample/*.json`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/task_entry_contract_v1.md`
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md`

The closure object is **not** part of the packet truth interface and therefore does not require a packet schema change. The closure belongs to a separate feedback-side surface that joins to the packet by `(line_id, packet_version, variation_id)`.

If a future Phase D.x implementation wave needs persisted shape, it must:

- introduce a separate schema (e.g. `schemas/feedback/matrix_script/publish_feedback_closure.schema.json`) **additive** to the repository;
- not modify the existing Matrix Script packet schema;
- not redesign packet truth;
- not replace any A/B/C frozen contract section.

Phase D.0 explicitly states: **no schema change is required at the contract-freeze step.**

## Mapping note · Phase C delivery projection → Phase D feedback closure

This mapping is informational. It documents how the closure joins to delivery projection without making the closure a writer of delivery projection.

| Phase C delivery projection field | Phase D closure field | Origin | In scope for Phase D writes? |
|---|---|---|---|
| `delivery_pack[].deliverable_id` | implicit row scope (per-deliverable feedback is **out of Phase D.0 scope**) | derived | no |
| `result_packet_binding.cell_slot_bindings[].cell_id` | `variation_feedback[].variation_id` (join key) | join only | no — read for join |
| `result_packet_binding.cell_slot_bindings[].slot_id` | (informational) | join only | no |
| `manifest.line_id` | `closure.line_id` | copied at creation; not authoritative on closure | no — closure copies once |
| `manifest.packet_version` | `closure.packet_version` | copied at creation | no — closure copies once |
| `manifest.deliverable_profile_ref` | (informational; no closure field) | not bound | no |
| `manifest.asset_sink_profile_ref` | (informational; no closure field) | not bound | no |
| `metadata_projection.metadata.*` | (informational; not part of closure) | not bound | no |
| `phase_d_deferred.*` | resolved by this contract | n/a | n/a |

### Variation-id join rule

The single canonical join from delivery to feedback is:

`packet.line_specific_refs[ref_id=matrix_script_variation_matrix].delta.cells[].cell_id`
→ `matrix_script_publish_feedback_closure_v1.variation_feedback[].variation_id`

There is no other join key. `cell_id` is the only variation identifier shared between Phase B/C truth and Phase D closure.

### Operator action vs platform callback

| Closure field / event | Origin |
|---|---|
| `publish_url` | operator action; or platform callback overwrites with canonical URL |
| `publish_status` | operator action for `pending` / `retracted`; platform callback for `published` / `failed` |
| `channel_metrics` | platform callback / metrics provider only |
| `operator_publish_notes` | operator action only |
| `feedback_closure_records[event_kind=operator_*]` | operator action |
| `feedback_closure_records[event_kind=platform_callback]` | platform callback |
| `feedback_closure_records[event_kind=metrics_snapshot]` | metrics provider |

### Out of Phase D scope (explicit)

The following are intentionally **not** part of Phase D, and remain undefined here:

- per-deliverable feedback (Phase D.0 is variation-level only);
- multi-channel arbitration / channel routing policy;
- provider / model / vendor / engine selection;
- runtime publish orchestration;
- automated retry / backoff / cancellation of publish attempts;
- Digital Anchor publish feedback;
- Hot Follow publish feedback;
- W2.2 / W2.3 scope;
- packet schema or sample changes;
- workbench presenter or delivery presenter changes;
- frontend rebuild;
- write-back implementation paths (HTTP, queue, callback handler, persistence);
- ACL / auth model for closure mutation;
- analytics dashboards;
- cross-line feedback aggregation.

## Forbidden in Phase D.0

Phase D.0 must not introduce or modify:

- any line of write-back implementation code;
- any change to `gateway/app/services/matrix_script/delivery_binding.py`;
- any change to `gateway/app/services/matrix_script/workbench_variation_surface.py`;
- any new field in the Matrix Script packet schema or sample;
- any provider / model / vendor / engine controls;
- Digital Anchor scope;
- Hot Follow scope;
- W2.2 / W2.3 scope;
- truth-shape state fields in packet, entry, workbench, or delivery surfaces;
- any redefinition of `manifest.*` or `metadata_projection.*` ownership;
- any change to Phase A/B/C contract files.

## Acceptance

Phase D.0 is green only when:

1. the publish feedback closure truth is explicitly defined as `matrix_script_publish_feedback_closure_v1` with `variation_feedback[]`, `feedback_closure_records[]`, and the field shapes above;
2. ownership and mutability are explicit, including the per-field origin (operator vs platform vs system);
3. the boundary vs Phase A/B/C is explicit and forbids mutation of packet, entry, workbench, delivery, manifest, and metadata projection;
4. the schema impact is explicitly stated as **no change to packet schema/sample** at this freeze step, with additive-only guidance for any later persistence work;
5. no A/B/C frozen truth is rewritten;
6. evidence / log / index write-back is complete;
7. the result is reviewable as one isolated contract wave with no implementation code attached.

## Remaining blockers before Phase D implementation (Phase D.1+)

Phase D implementation may not start until:

1. Phase C is signed off (PASS confirmed in instruction).
2. This Phase D.0 contract is reviewed and accepted.
3. A Phase D.1 brief is issued that explicitly authorizes write-back implementation, names the persistence surface, and confirms it does not turn Phase C projection into a mutable owner.
4. The variation-id join rule remains the single canonical join into closure truth.

## Operator review zone tag (additive, OWC-MS PR-2 — 2026-05-05)

Authority: `docs/reviews/owc_ms_gate_spec_v1.md` §3 MS-W5 — "four review affordances (字幕 / 配音 / 文案 / CTA) writing through existing closure `operator_note` event with an additive structured `review_zone` field (closed enum: `subtitle / dub / copy / cta`). Closure shape unchanged; an enum closed-set extension on event payload is the only contract touch."

This addendum extends the `operator_note` event payload with one optional field. It introduces no new field on `variation_feedback[]`, no new field on the closure-wide envelope, and no new event kind.

### Closed enum

```
review_zone ∈ { "subtitle", "dub", "copy", "cta" }
```

These four zones map 1:1 onto the matrix_script_product_flow §6.1D Workbench D 校对区 affordances and are the binding-and-exhaustive set for OWC-MS PR-2. Any future widening requires a separate gate-spec authoring step.

### Payload shape

`operator_note` events MAY carry an additional `payload.review_zone` value drawn from the closed enum above. The existing required field `payload.operator_publish_notes` is unchanged. Legacy `operator_note` events without `review_zone` remain valid.

```
{
  "event_kind": "operator_note",
  "actor_kind": "operator",
  "variation_id": "<cell_id>",
  "payload": {
    "operator_publish_notes": "<operator note text>",
    "review_zone": "subtitle"   // OPTIONAL · closed enum above
  }
}
```

### Validation rule

When `payload.review_zone` is present on an `operator_note` event, it MUST be a member of the closed enum; otherwise the closure raises `ClosureValidationError` (HTTP 400 at the operator endpoint). The validator does not auto-fill `review_zone`; an operator may submit a legacy untagged note. The validator does NOT accept `review_zone` on any other event kind (`operator_publish` / `operator_retract` / `platform_callback` / `metrics_snapshot`).

### Recorded position

When the validation passes, the value is recorded as an additional optional key on the appended `feedback_closure_records[]` entry only:

```
record = {
  "event_id": ...,
  "variation_id": ...,
  "event_kind": "operator_note",
  "recorded_at": ...,
  "actor_kind": "operator",
  "payload_ref": ...,
  "review_zone": "subtitle"        // present iff the validated event carried it
}
```

The `variation_feedback[]` row is not mutated by the additional tag. The closure-wide shape (`surface`, `closure_id`, `line_id`, `packet_version`, `variation_feedback`, `feedback_closure_records`) is not extended.

### What this addendum does NOT do

- It does not introduce a new event kind. `operator_note` remains the single review-write event kind.
- It does not introduce a new actor kind; the `operator_note → operator` mapping is unchanged.
- It does not widen `EVENT_KINDS`, `ACTOR_KINDS`, or `CHANNEL_METRICS_KEYS`.
- It does not change the closure-shape envelope, the per-row `variation_feedback[]` shape, or the closure-wide `publish_status` aggregator.
- It does not add a new endpoint; review actions write through the existing `POST /api/matrix-script/closures/{task_id}/events` route per Recovery PR-3.
- It does not introduce per-zone aggregate state on the closure; consumers that need per-zone history MUST replay `feedback_closure_records[]`.
- It does not interact with Hot Follow / Digital Anchor closures.

### Schema impact

- `schemas/`: unchanged (no per-event JSON schema lives in `schemas/` for this surface today; `EVENT_KINDS` / `REVIEW_ZONE_VALUES` are owned by `gateway/app/services/matrix_script/publish_feedback_closure.py`).
- `docs/contracts/matrix_script/packet_v1.md`: unchanged.
- `docs/contracts/matrix_script/task_entry_contract_v1.md`: unchanged.
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`: unchanged.
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md`: unchanged.

This addendum is the only contract touch in OWC-MS PR-2. All other PR-2 work is pure projection over existing truth.
