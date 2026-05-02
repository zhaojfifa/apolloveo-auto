# Digital Anchor Publish Feedback Write-back Contract v1 (Phase D.1)

Date: 2026-05-02
Status: Plan B contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **no write-back code in this wave**.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan B
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md` (Phase D.0 closure shape)
- `docs/contracts/digital_anchor/delivery_binding_contract_v1.md` (Phase C boundary)
- `docs/contracts/digital_anchor/packet_v1.md` (frozen packet truth)
- Mirror reference: `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md`
- `docs/contracts/status_ownership_matrix.md`

## Purpose

Extend the Digital Anchor Phase D.0 closure shape into the Phase D.1 **write-back direction**. The Phase D.0 contract froze the closure object and read-side truth; this contract freezes the rules under which closure events may be **mirrored back into the closure store**, and the rules that protect upstream truth from being corrupted by the write-back path.

This contract does **not** implement write-back code, define HTTP/queue handlers, or specify ACL/auth. It pins the contract truth that any future Phase D.1 implementation must obey.

## Boundary statement (binding)

The Phase D.0 boundary is reasserted and extended:

1. **Phase C delivery binding remains read-only.** Write-back MUST NOT mutate `delivery_pack`, `result_packet_binding`, `manifest`, or `metadata_projection`.
2. **Packet truth remains immutable from this path.** Write-back MUST NOT mutate any packet `generic_refs[]`, `line_specific_refs[]`, `binding`, `evidence`, or `metadata` field.
3. **Upstream line-specific contract objects (`role_pack`, `speaker_plan`) are read-only from this path.** Write-back MUST NOT amend role enumeration, segment enumeration, or any closed kind-set.
4. **Phase D owns feedback closure only.** Write-back targets only the `digital_anchor_publish_feedback_closure_v1` object.
5. **Forbidden state-shape fields remain banned outside the closure.** `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable` MUST NOT be written into packet, delivery, or workbench surfaces by this path. The scoped `publish_status` enum lives only inside the closure.

## Closed write-back event set

Write-back is **append-only into `feedback_closure_records[]`** plus per-row mutation of feedback fields under explicit ownership. The closed set of write-back event kinds is:

| `event_kind`            | actor_kind | trigger source                                          | mutates                                                                  |
| ----------------------- | ---------- | ------------------------------------------------------- | ------------------------------------------------------------------------ |
| `publish_attempted`     | operator   | operator initiates publish from delivery surface        | appends record; sets `role_feedback[].publish_status`/`segment_feedback[].publish_status` to `pending` |
| `publish_accepted`      | platform   | external platform callback acknowledges publish         | appends record; sets `publish_status` to `published`; sets canonical `publish_url`; updates `channel_metrics` snapshot |
| `publish_rejected`      | platform   | external platform callback reports failure              | appends record; sets `publish_status` to `failed`                        |
| `publish_retracted`     | operator   | operator retracts a previously-published row            | appends record; sets `publish_status` to `retracted`                     |
| `metrics_snapshot`      | platform   | metrics provider records a snapshot                     | appends record; appends to `channel_metrics` per the Phase D.0 shape     |
| `operator_note`         | operator   | operator records a free-text publish note               | appends record; sets `operator_publish_notes`                            |

`publish_status` values mirror the Phase D.0 closed enum: `{ pending, published, failed, retracted }`. Any other value is forbidden. Any event_kind outside this closed set is forbidden.

## Append-only discipline

- `feedback_closure_records[]` is append-only. Edits and deletes are forbidden. Corrections are recorded as new events.
- Per-row mutable fields (`publish_url`, `publish_status`, `channel_metrics`, `operator_publish_notes`, `last_event_id`) follow last-write-wins per closure event; the audit trail is the source of truth, mutable fields are the cached current view.
- Channel metrics snapshots are append-only; an existing snapshot MUST NOT be overwritten in place.

## Per-row scope (role + segment)

Digital Anchor write-back operates at **two row scopes**:

- `role_feedback[]` — keyed by `role_id` from `digital_anchor_role_pack.delta.roles[].role_id`.
- `segment_feedback[]` — keyed by `segment_id` from `digital_anchor_speaker_plan.delta.segments[].segment_id`.

Each event_kind targets exactly one row (role OR segment) per write. A single operator action that affects multiple rows MUST split into one event per row (each appended atomically into `feedback_closure_records[]`).

These per-row scopes mirror the Matrix Script analogue's `variation_feedback[].variation_id` join (per `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` §"Variation-id join rule"), with role+segment replacing variation as the closed Digital Anchor join keys.

## Timestamping discipline

- All `recorded_at` timestamps are ISO-8601 UTC, second precision or finer.
- Within a single closure object, `recorded_at` per row MUST be monotonic non-decreasing per `(row_scope, row_id)`. A late-arriving event (network reordering) with a lower timestamp than the current `last_event_id` MUST be rejected at the contract surface; a re-issuance with a fresh timestamp is the correction path.
- Cross-row ordering is NOT guaranteed monotonic.

## Forbidden in write-back path

- vendor / model / provider / engine / avatar-engine / TTS-provider / lip-sync-engine identifiers in any event payload, response, or stored row;
- donor (SwiftCraft) module identifiers;
- mutation of any non-publish-feedback ref (packet, role_pack, speaker_plan, delivery binding, manifest, metadata_projection);
- cross-line write-back (no Matrix Script, no Hot Follow);
- new advisory codes outside the Hot Follow advisory taxonomy (the closure does not own advisory truth — that lives behind the Plan D `l4_advisory_producer_output_contract_v1.md`);
- raw publish payload bodies — only opaque `payload_ref` is stored;
- ACL/auth model for closure mutation (out of scope; declared in implementation gate).

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier appears in any closed-set field, event payload, or row.
- Validator R5: `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable` are not written outside the scoped `publish_status` enum.
- Phase D.0 boundary statement (closure contract §"Phase Boundary Statement") is reasserted verbatim.

## Acceptance

This contract is green when:

1. The closed write-back event set is exhaustive — no event kind outside the table above may be appended.
2. Append-only discipline is binding for `feedback_closure_records[]` and `channel_metrics` snapshots.
3. Per-row scope is exactly `role_feedback[].role_id` or `segment_feedback[].segment_id`; no other join exists.
4. Timestamping is UTC ISO-8601, monotonic per `(row_scope, row_id)`.
5. No upstream truth (packet, role_pack, speaker_plan, delivery binding, manifest, metadata_projection) is mutated by this path.

## What this contract does NOT do

- Does not implement write-back HTTP / queue / callback handlers (Plan E gate).
- Does not change Phase D.0 closure shape.
- Does not change Digital Anchor packet schema.
- Does not authorize cross-line aggregation.
- Does not unblock Platform Runtime Assembly.
- Does not unblock Capability Expansion.
- Does not unblock frontend patching.

## References

- `docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md`
- `docs/contracts/digital_anchor/delivery_binding_contract_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
