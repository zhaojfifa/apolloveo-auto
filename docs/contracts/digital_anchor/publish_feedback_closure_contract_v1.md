# Digital Anchor Publish Feedback Closure Contract v1

Date: 2026-04-28
Status: Phase D.0 landing (Digital Anchor Second Production Line Wave - Publish Feedback Closure Contract Freeze)
Authority:
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Part III P2
- `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`
- `docs/contracts/digital_anchor/delivery_binding_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `schemas/packets/digital_anchor/packet.schema.json`

## Purpose

Define the formal Phase D publish feedback closure contract for Digital Anchor.

This contract freezes the feedback closure object and write-back truth shape for:

1. role-level feedback;
2. segment-level feedback;
3. publish URL;
4. publish status;
5. channel metrics;
6. operator publish notes;
7. feedback closure records.

This Phase D.0 wave is contract-only. It does not implement write-back code, does not mutate Phase C delivery projection, and does not change the Digital Anchor packet schema.

## Phase Boundary Statement

Phase C delivery binding remains read-only. Its `delivery_pack`, `result_packet_binding`, `manifest`, and `metadata_projection` sections stay projection-only and must not become feedback owners.

Phase D owns feedback closure only. Phase D does not rewrite:

- Phase A task / role entry truth;
- Phase B workbench role / speaker surface truth;
- Phase C delivery binding projection truth;
- packet `generic_refs[]`;
- packet `line_specific_refs[]`;
- packet `binding`;
- packet `evidence`;
- packet `metadata`;
- `manifest.*`;
- `metadata_projection.*`.

Forbidden truth-shape state fields remain banned in packet and delivery projection surfaces: unscoped `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, and `publishable`.

The only allowed status-like field in this contract is the scoped feedback field `publish_status`, owned by the publish feedback closure object. It is not a packet readiness field, not a delivery readiness field, and not a task state field.

## Feedback Closure Object

The formal Phase D closure object is named `digital_anchor_publish_feedback_closure_v1`.

It is a separate write-back object keyed by:

| Field | Source / rule |
|---|---|
| `line_id` | fixed `digital_anchor` |
| `packet_version` | copied from packet `packet_version` |
| `delivery_manifest_id` | copied from Phase C `manifest.manifest_id` |
| `deliverable_profile_ref` | copied from Phase C `manifest.deliverable_profile_ref` |
| `asset_sink_profile_ref` | copied from Phase C `manifest.asset_sink_profile_ref` |
| `role_feedback[]` | role-level feedback rows defined below |
| `segment_feedback[]` | segment-level feedback rows defined below |
| `publish_url` | platform callback/result or operator-provided URL |
| `publish_status` | platform callback/result or operator closure action |
| `channel_metrics` | platform callback/result metrics snapshot |
| `operator_publish_notes` | operator-authored closure note |
| `feedback_closure_records[]` | append-only closure events |

The closure object is additive Phase D truth. It is not embedded into the Digital Anchor packet v1 schema in Phase D.0.

## Role-Level Feedback Object

`role_feedback[]` records feedback against a role declared by `digital_anchor_role_pack.delta.roles[]`.

| Field | Owner | Source / rule |
|---|---|---|
| `role_id` | system join | must match `role_pack.delta.roles[].role_id` |
| `role_display_name` | projection | copied from `role_pack.delta.roles[].display_name` for display only |
| `role_feedback_kind` | operator | closed labels: `accepted`, `needs_revision`, `not_used` |
| `role_feedback_note` | operator | optional note; no provider/vendor/model content |
| `linked_segments[]` | projection | segment ids whose `binds_role_id` equals this `role_id` |

Role feedback must not mutate role declarations, role framing, appearance refs, or language scope refs.

## Segment-Level Feedback Object

`segment_feedback[]` records feedback against a speaker segment declared by `digital_anchor_speaker_plan.delta.segments[]`.

| Field | Owner | Source / rule |
|---|---|---|
| `segment_id` | system join | must match `speaker_plan.delta.segments[].segment_id` |
| `binds_role_id` | projection | copied from `speaker_plan.delta.segments[].binds_role_id` |
| `script_ref` | projection | copied from `speaker_plan.delta.segments[].script_ref` |
| `segment_feedback_kind` | operator | closed labels: `accepted`, `needs_revision`, `not_used` |
| `audio_feedback_note` | operator | optional note on audio/dub result; no provider/vendor/model content |
| `lip_sync_feedback_note` | operator | optional note on lip-sync result; no provider/vendor/model content |
| `subtitle_feedback_note` | operator | optional note on subtitle result; no provider/vendor/model content |

Segment feedback must not mutate segment declarations, script refs, dub kind, lip-sync kind, language pick, or role binding.

## Publish URL

`publish_url` is the external URL or platform destination returned by a publish callback/result or entered by an operator during closure.

Rules:

- optional until a publish action exists;
- must not be used as delivery readiness;
- must not rewrite Phase C `manifest`;
- must not imply provider, model, engine, avatar-engine, TTS provider, or lip-sync engine identity.

## Publish Status

`publish_status` is scoped to the feedback closure object and may take only:

- `not_published`
- `published`
- `publish_failed`
- `archived`

Rules:

- `publish_status` is not packet `ready_state`;
- `publish_status` is not delivery readiness;
- `publish_status` is not a task lifecycle state;
- Phase C must not project `publish_status`.

## Channel Metrics

`channel_metrics` is an optional platform callback/result snapshot.

Allowed fields:

| Field | Rule |
|---|---|
| `views` | integer snapshot |
| `likes` | integer snapshot |
| `shares` | integer snapshot |
| `comments` | integer snapshot |
| `watch_seconds` | integer snapshot |
| `captured_at` | timestamp string |

Channel metrics are feedback closure truth only. They must not mutate delivery manifest, packet metadata, role pack, or speaker plan.

## Operator Publish Notes

`operator_publish_notes` is operator-authored closure text.

Rules:

- may reference role ids and segment ids;
- must not introduce provider/vendor/model controls;
- must not rewrite packet `metadata.notes`;
- must not replace role-level or segment-level structured feedback.

## Feedback Closure Records

`feedback_closure_records[]` is append-only and records closure events.

| Field | Owner | Rule |
|---|---|---|
| `record_id` | system | stable id for this closure record |
| `recorded_at` | system | timestamp string |
| `recorded_by` | system/operator | actor id or role label |
| `record_kind` | system/operator | `operator_review`, `publish_callback`, `archive_action`, `correction_note` |
| `role_ids[]` | projection/operator | optional affected role ids; must resolve to role pack |
| `segment_ids[]` | projection/operator | optional affected segment ids; must resolve to speaker plan |
| `note` | operator/platform | closure note; no provider/vendor/model content |

Records are append-only. Implementations must not edit previous records except through an explicit corrective record.

## Ownership and Mutability

| Object / field family | Owner in Phase D | Mutable? | Notes |
|---|---|---|---|
| `role_feedback[]` | publish feedback closure | yes | additive write-back only |
| `segment_feedback[]` | publish feedback closure | yes | additive write-back only |
| `publish_url` | publish feedback closure | yes | platform/operator supplied |
| `publish_status` | publish feedback closure | yes | scoped closure field only |
| `channel_metrics` | publish feedback closure | yes | platform snapshot |
| `operator_publish_notes` | publish feedback closure | yes | operator-authored |
| `feedback_closure_records[]` | publish feedback closure | append-only | event log |
| Phase A entry fields | Phase A contract | no | not rewritten by Phase D |
| Phase B role / speaker surfaces | Phase B contract | no | not rewritten by Phase D |
| Phase C delivery binding | Phase C contract | no | remains read-only |
| `manifest.*` | Phase C projection | no | display-only |
| `metadata_projection.*` | Phase C projection | no | display-only |
| packet schema / sample | packet contract | no in D.0 | no schema change in this wave |

## Additive Truth vs Projection-Only

Additive Phase D truth:

- `digital_anchor_publish_feedback_closure_v1.role_feedback[]`;
- `digital_anchor_publish_feedback_closure_v1.segment_feedback[]`;
- `digital_anchor_publish_feedback_closure_v1.publish_url`;
- `digital_anchor_publish_feedback_closure_v1.publish_status`;
- `digital_anchor_publish_feedback_closure_v1.channel_metrics`;
- `digital_anchor_publish_feedback_closure_v1.operator_publish_notes`;
- `digital_anchor_publish_feedback_closure_v1.feedback_closure_records[]`.

Projection-only:

- Phase C `delivery_pack`;
- Phase C `result_packet_binding`;
- Phase C `manifest`;
- Phase C `metadata_projection`;
- Phase B `role_surface`;
- Phase B `speaker_surface`;
- Phase B `role_segment_binding_surface`;
- packet refs / binding / evidence / metadata.

## Schema Impact Note

No packet/schema change is needed in Phase D.0.

Reason:

- the current Digital Anchor packet v1 is the line truth interface for entry/workbench/delivery projection;
- feedback closure is downstream publish feedback truth, not packet admission truth;
- embedding feedback fields into packet v1 would mix post-delivery mutable closure state into the frozen packet interface.

If a future Phase D implementation requires persistence schema, it must be additive and external to the packet schema, using the `digital_anchor_publish_feedback_closure_v1` object defined here. It must not replace existing A/B/C frozen sections and must not redesign packet truth.

## Mapping Note

| Delivery projection field | Feedback closure field | Source owner |
|---|---|---|
| `manifest.line_id` | `line_id` | projection copy |
| `manifest.packet_version` | `packet_version` | projection copy |
| `manifest.manifest_id` | `delivery_manifest_id` | projection copy |
| `manifest.deliverable_profile_ref` | `deliverable_profile_ref` | projection copy |
| `manifest.asset_sink_profile_ref` | `asset_sink_profile_ref` | projection copy |
| `result_packet_binding.role_segment_bindings[].role_id` | `role_feedback[].role_id` | join key |
| `result_packet_binding.role_segment_bindings[].segment_id` | `segment_feedback[].segment_id` | join key |
| `result_packet_binding.role_segment_bindings[].binds_role_id` | `segment_feedback[].binds_role_id` | projection copy |
| `delivery_pack.deliverables[]` | `feedback_closure_records[].note` / affected ids | operator/platform interpretation |

Role / segment join rule:

`speaker_plan.delta.segments[].binds_role_id == role_pack.delta.roles[].role_id`

Operator action supplies:

- `role_feedback_kind`;
- `role_feedback_note`;
- `segment_feedback_kind`;
- `audio_feedback_note`;
- `lip_sync_feedback_note`;
- `subtitle_feedback_note`;
- `operator_publish_notes`;
- corrective `feedback_closure_records[]`.

Platform callback/result supplies:

- `publish_url`;
- `publish_status`;
- `channel_metrics`;
- callback-origin `feedback_closure_records[]`.

Out of scope:

- provider/model/vendor/avatar-engine/TTS/lip-sync controls;
- Phase C delivery projection mutation;
- manifest ownership mutation;
- packet schema redesign;
- Matrix Script;
- Hot Follow;
- W2.2 / W2.3.

## Acceptance

Phase D.0 is green only when:

1. Phase D feedback closure truth is explicitly defined;
2. ownership boundary versus Phase C is explicit;
3. schema impact is explicit and no packet schema change is required in this wave;
4. A/B/C frozen truth is not rewritten;
5. evidence/write-back is complete;
6. the result is reviewable as one isolated contract wave.

## Remaining Blockers Before Phase D Implementation

Phase D implementation may not start until this contract is reviewed and accepted. Implementation must add write-back logic against the separate feedback closure object without mutating Phase C delivery projection, packet schema, manifest, or metadata projection.
