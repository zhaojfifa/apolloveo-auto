# Digital Anchor Create-Entry Payload Builder Contract v1

Date: 2026-05-02
Status: Plan B contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **no implementation in this wave**.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan B
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/digital_anchor/task_entry_contract_v1.md` (Phase A entry)
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md` (`digital_anchor` row)
- Mirror reference: `gateway/app/services/matrix_script/create_entry.py` (Matrix Script analogue; do not replicate behavior, replicate shape)

## Purpose

Pin the **single legal seeding path** from the closed Digital Anchor entry field set (defined in `task_entry_contract_v1`) onto the existing task repository payload + Digital Anchor packet shape. This contract freezes:

1. the closed input shape (mirrors the Phase A entry contract);
2. the closed output payload shape (line-id, route stub, packet seed with `line_specific_refs[]`);
3. the per-field mapping rule (verbatim from `task_entry_contract_v1` §"Mapping note");
4. the seeding discipline (only Phase A scaffolding seeded; no Phase B authoring; no `roles[]` / `segments[]` enumeration).

This contract does **not** authorize or describe runtime implementation. It does not introduce a new entry field, widen any closed kind-set, or mutate Digital Anchor packet truth.

## Ownership

- Owner: contract layer (Plan B).
- Future runtime consumer: a Digital Anchor `create_entry` module under `gateway/app/services/digital_anchor/` (Plan E gate; not in this wave).
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend platform.

## Inputs (closed)

The builder accepts **exactly** the eleven-field closed entry set frozen in [docs/contracts/digital_anchor/task_entry_contract_v1.md](task_entry_contract_v1.md) §"Entry field set":

Required: `topic`, `source_script_ref`, `language_scope`, `role_profile_ref`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint`.

Optional: `dub_kind_hint`, `lip_sync_kind_hint`, `scene_binding_hint`, `operator_notes`.

Any unknown field MUST cause the builder to reject the input. Forbidden field set is reasserted from the entry contract: no `vendor_id`, `model_id`, `provider_id`, `engine_id`, no avatar-engine / TTS-provider / lip-sync-engine identifier, no `donor_*`, `swiftcraft_*`, no state-shape field (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`).

## Outputs (closed)

The builder produces a single payload with the following closed top-level shape. No additional keys may be added without re-versioning this contract.

```
{
  task_id: <opaque, builder-assigned>,
  id: <same as task_id>,
  kind: "digital_anchor",
  category_key: "digital_anchor",
  category: "digital_anchor",
  platform: "digital_anchor",
  title: <entry.topic>,
  source_url: <entry.source_script_ref>,
  content_lang: <entry.language_scope.target_language[0]>,
  ui_lang: "zh",
  status: "pending",          # repository column only — NOT packet truth
  last_step: null,
  error_message: null,
  config: {
    line_id: "digital_anchor",
    entry_contract: "digital_anchor_task_entry_v1",
    entry: { ... closed entry field set verbatim ... },
    next_surfaces: {
      workbench: "/tasks/<task_id>",
      delivery:  "/tasks/<task_id>/publish"
    }
  },
  packet: {
    line_id: "digital_anchor",
    packet_version: "v1",
    metadata: { notes: <semicolon-joined operator-hint trail> },
    line_specific_refs: [
      { ref_id: "digital_anchor_role_pack",
        path:   "docs/contracts/digital_anchor/role_pack_contract_v1.md",
        version: "v1",
        binds_to: ["factory_input_contract_v1"] },
      { ref_id: "digital_anchor_speaker_plan",
        path:   "docs/contracts/digital_anchor/speaker_plan_contract_v1.md",
        version: "v1",
        binds_to: ["factory_audio_plan_contract_v1",
                   "factory_language_plan_contract_v1",
                   "factory_scene_plan_contract_v1"] }
    ]
  },
  line_specific_refs: [ ... mirrors packet.line_specific_refs[] ... ]
}
```

The `status: "pending"` field is a task-repository row column required by the existing repository normalizer; it is **not** packet truth and is **not** L1/L3/L4 state. Validator R5 forbids attaching `status` to packet truth; this builder does not.

## Mapping rule (entry → packet) — verbatim

The builder MUST apply the mapping verbatim from [docs/contracts/digital_anchor/task_entry_contract_v1.md](task_entry_contract_v1.md) §"Mapping note (entry → packet)". This contract pins that mapping as the single legal seeding path; it does not redeclare it, and it MUST NOT diverge.

Summary (canonical text in the entry contract):

- `entry.topic`, `entry.output_intent`, `entry.operator_notes` → `packet.metadata.notes` (free-form trail).
- `entry.source_script_ref` → opaque handle carried into Phase B authoring of `line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.segments[*].script_ref`. Builder seeds the ref skeleton only.
- `entry.language_scope` → opaque handle carried into Phase B authoring of `digital_anchor_role_pack.delta.roles[*].language_scope_ref` + `digital_anchor_speaker_plan.delta.segments[*].language_pick`.
- `entry.role_profile_ref` → opaque handle carried into Phase B authoring of `digital_anchor_role_pack.delta.roles[*].appearance_ref`.
- `entry.role_framing_hint`, `entry.dub_kind_hint`, `entry.lip_sync_kind_hint`, `entry.scene_binding_hint`, `entry.speaker_segment_count_hint` → Phase B authoring scaffolding (out of packet entirely; recorded in `metadata.notes` trail per entry contract).

The builder seeds **only** the two `line_specific_refs[]` skeletons named above. It does NOT author `roles[]`, `segments[]`, `framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`, capability plan, binding profile refs, or evidence — these belong to the existing line-specific contracts (Phase B authoring) and to the static line packet (per `packet_v1.md` §Capability plan / §Binding profiles).

## Seeding discipline (normative)

1. Builder MUST reject input that fails the closed-set test in `task_entry_contract_v1`.
2. Builder MUST seed exactly the two `line_specific_refs[]` rows declared above; it MUST NOT add a third.
3. Builder MUST NOT widen any closed kind-set.
4. Builder MUST NOT compute or attach `evidence.ready_state`, `current_attempt`, `final_provenance`, or any L3/L4 field.
5. Builder MUST NOT name a vendor / model / provider / engine / avatar-engine / TTS-provider / lip-sync-engine.
6. Builder MUST NOT cross into Matrix Script, Hot Follow, or W2.2 / W2.3 scope.
7. Builder output MUST normalize through the existing repository `normalize_task_payload` invariants (mirrors Matrix Script analogue) — the payload shape is the only contract surface, not the normalization step itself.

## Validator alignment

- Envelope rule E4 (line packet shape): the seeded packet matches `digital_anchor` packet envelope; refs reference existing contract paths.
- Validator R3 (no vendor/model/provider/engine identifiers): satisfied by the closed entry set + closed output shape; no field on either side names a donor concept.
- Validator R5 (no truth-shape state field on packet): the `status: "pending"` task row column is repository-side only; the seeded packet carries no `status`/`ready`/`done`/etc.

## What this contract does NOT do

- Does not authorize implementation in this wave (Plan E gate only).
- Does not redefine the entry field set.
- Does not introduce the `/tasks/digital-anchor/new` route — that is the sibling Plan B contract (`new_task_route_contract_v1.md`).
- Does not author `roles[]` or `segments[]`.
- Does not touch Matrix Script, Hot Follow, W2.2 / W2.3.
- Does not unblock Platform Runtime Assembly.
- Does not unblock Capability Expansion.
- Does not unblock frontend patching.

## Acceptance

This contract is green when:

1. Every required entry field maps to exactly one packet path or the `metadata.notes` trail per the verbatim mapping rule.
2. The output payload shape is the closed shape declared above; no key has been added or omitted.
3. Closed kind-sets are not widened.
4. No Phase B / C / D authoring leaks into the seeded packet.
5. No forbidden key (vendor / model / provider / engine / donor / state-shape) appears in either input or output.

## References

- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `gateway/app/services/matrix_script/create_entry.py` (mirror analogue, read-only reference)
- `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md` (Matrix Script alignment template; this contract is the Digital Anchor analogue at contract-level)
