# Matrix Script `result_packet_binding` Artifact-Lookup Contract v1

Date: 2026-05-02
Status: Plan B contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **resolves the `not_implemented_phase_c` placeholder at the spec surface**. Code change is gated to Plan E.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan B (Matrix Script `result_packet_binding` artifact-lookup contract)
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (Phase C boundary)
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/publish_readiness_contract_v1.md` (Plan D — `final_provenance` shape)
- Reference: `gateway/app/services/matrix_script/delivery_binding.py:93-125` (the five `not_implemented_phase_c` placeholders this contract pins)

## Purpose

Pin the contract for the **artifact-lookup function** that resolves a Matrix Script Phase C deliverable row to its current artifact handle. Today, [gateway/app/services/matrix_script/delivery_binding.py:93](../../gateway/app/services/matrix_script/delivery_binding.py:93) emits `"artifact_lookup": "not_implemented_phase_c"` on five deliverable rows (`matrix_script_variation_manifest`, `matrix_script_slot_bundle`, `matrix_script_subtitle_bundle`, `matrix_script_audio_preview`, `matrix_script_scene_pack`). Gap review §7.2 names this as the reason the Matrix Script Delivery Center is not yet operator-trial-eligible end-to-end.

This contract:

1. Specifies the lookup function's input shape;
2. Specifies the lookup function's output shape;
3. Specifies the resolution rule (read-only over packet truth);
4. Specifies the failure mode (explicit enumerated absence; never throws, never fabricates);
5. Reasserts the Phase C boundary so the lookup remains a projection, never a writer.

This contract does **not** implement the lookup. The implementation lands when Plan E gate opens. The placeholder string `not_implemented_phase_c` will be replaced with calls to the function described here.

## Ownership

- Owner: contract layer (Plan B).
- Future runtime consumer: `gateway/app/services/matrix_script/delivery_binding.py::project_delivery_binding()` (Plan E gate).
- Non-owners: workers, storage providers, vendor adapters, presenters, frontend.

## Function shape

```
artifact_lookup(packet, ref_id, locator) -> ArtifactHandle | "artifact_lookup_unresolved"
```

### Inputs

| Param      | Type                | Source                                                                 |
| ---------- | ------------------- | ---------------------------------------------------------------------- |
| `packet`   | Mapping             | the Matrix Script packet instance the projection is rendering          |
| `ref_id`   | enum (closed)       | one of: `matrix_script_variation_matrix`, `matrix_script_slot_pack`, `capability:dub`, `capability:pack`, `capability:subtitles` |
| `locator`  | scalar (closed)     | `cell_id` (when `ref_id=matrix_script_variation_matrix`) OR `slot_id` (when `ref_id=matrix_script_slot_pack`) OR `null` (when `ref_id` is a `capability:*` deliverable lookup) |

The `(ref_id, locator)` pair MUST be one of the closed pairs declared in [docs/contracts/matrix_script/delivery_binding_contract_v1.md](delivery_binding_contract_v1.md) §"Visible deliverables" + §"Result packet binding visualization" `cell_slot_bindings[]`. Any other pair returns `artifact_lookup_unresolved`.

### Outputs

```
ArtifactHandle = {
  artifact_ref:    string,                   # opaque catalog handle
  freshness:       "fresh" | "stale" | "absent",
  provenance:      "current" | "historical"  # mirrors L3 final_provenance (Plan D)
}
```

`artifact_lookup_unresolved` is a contract-level enumerated absence (a sentinel string). It is **not** an exception, **not** a `None`, and **not** an empty `ArtifactHandle`. Consumers MUST distinguish `artifact_lookup_unresolved` from a successful resolution to a stale or absent artifact.

The `provenance` field carries the same closed enum as the L3 `final_provenance` field promoted by Plan D (`docs/contracts/hot_follow_current_attempt_contract_v1.md` once amended for D2). The lookup MUST mirror this enum verbatim — it does not invent a new provenance vocabulary.

## Resolution rule (normative)

The lookup function is a **pure projection** of packet truth:

1. Inputs read: `packet.line_specific_refs[ref_id=...]​.delta`, `packet.binding.capability_plan[]`, `packet.binding.deliverable_profile_ref`, `packet.binding.asset_sink_profile_ref`.
2. Outputs derived: from those reads, plus the `(ref_id, locator)` join key, return the matching opaque artifact handle.
3. **No I/O across runtime boundaries.** The lookup MUST NOT:
   - call worker gateways;
   - call storage providers (S3, blob stores, asset library backends);
   - resolve provider/vendor/model identifiers;
   - mutate the packet;
   - mutate the closure store;
   - emit advisories (advisory truth lives behind the Plan D advisory producer contract).
4. **No truth invention.** If the packet does not carry a resolvable handle for the `(ref_id, locator)` pair, the lookup returns `artifact_lookup_unresolved`. It does not fabricate a placeholder URL, generate a synthetic id, or reach into a sibling deliverable.
5. **Freshness derivation:** `freshness=fresh` when the resolved handle exists in the packet AND the packet's `final_fresh` (L2) is `true` for the bound row; `freshness=stale` when the handle exists but `final_fresh=false`; `freshness=absent` when no handle is reachable but the `(ref_id, locator)` pair is structurally valid.
6. **Provenance derivation:** `provenance` mirrors the L3 `final_provenance` field (Plan D) for the bound row. If L3 has not yet promoted `final_provenance` for the row, the lookup returns `artifact_lookup_unresolved` rather than guessing.

## Failure-mode discipline

- The function MUST NOT throw exceptions on missing or malformed packet sub-structures. Any condition that prevents resolution returns `artifact_lookup_unresolved`.
- `artifact_lookup_unresolved` MUST be carried verbatim into the rendered Phase C delivery row (replacing today's `"not_implemented_phase_c"` placeholder) so operator surfaces can render an explicit "unresolved" indication rather than blank.
- The function MUST NOT escalate `artifact_lookup_unresolved` to a publish-blocking advisory directly — that escalation is owned by the Plan D `publish_readiness_contract_v1` consumer.

## Forbidden in lookup path

- vendor / model / provider / engine identifiers in inputs, intermediate state, or outputs;
- storage URLs (the lookup returns opaque `artifact_ref` only — URL realization is a downstream presenter concern);
- mutation of any packet field (envelope rule E4);
- worker / adapter calls (production line runtime assembly remains BLOCKED);
- cross-line resolution (no Digital Anchor, no Hot Follow);
- truth-shape state writes (`status`, `ready`, `done`, `final_ready`, `publishable`).

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in input/output schema.
- Validator R5: no truth-shape state field in the `ArtifactHandle` shape; the `provenance` enum is the L3-owned closed enum, not a new readiness field.
- Phase C delivery boundary (per delivery binding contract) reasserted: the lookup is read-only.

## Acceptance

This contract is green when:

1. The `(ref_id, locator)` closed pair set covers exactly the five Phase C deliverable rows enumerated in the existing delivery binding contract.
2. The `ArtifactHandle` shape is the closed shape declared above; `provenance` reuses the Plan D L3 enum verbatim.
3. The failure mode is explicit `artifact_lookup_unresolved`; no exception, no fabrication.
4. The lookup is a pure projection — no I/O across runtime boundaries, no packet mutation.
5. The placeholder `"not_implemented_phase_c"` may be replaced one-for-one with this lookup once Plan E opens; no other code site changes.

## What this contract does NOT do

- Does not implement the lookup function (Plan E only).
- Does not change the Phase C delivery binding contract's deliverable enumeration.
- Does not redesign packet truth, schema, or sample.
- Does not introduce Digital Anchor scope.
- Does not introduce Hot Follow scope.
- Does not unblock Platform Runtime Assembly.
- Does not unblock Capability Expansion.
- Does not unblock frontend patching.

## References

- `docs/contracts/matrix_script/delivery_binding_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `gateway/app/services/matrix_script/delivery_binding.py` (read-only reference; placeholders at lines 93, 101, 109, 117, 125)
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
